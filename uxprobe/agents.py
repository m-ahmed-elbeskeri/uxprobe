"""Adapters for coding-CLI agents (claude, codex, gemini, cursor-agent, ...).

Each backend knows how to be invoked non-interactively, how to receive a long
prompt, and how to get the assistant's final text back out of whatever it prints.
Anything not covered here can be driven with `--agent custom --cmd "..."`.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable

PROMPT_TOKEN = "{prompt}"


class AgentError(RuntimeError):
    pass


# --------------------------------------------------------------------------
# extracting the report out of agent stdout
# --------------------------------------------------------------------------

_FENCE_RE = re.compile(r"```(?:json|JSON)?\s*\n(.*?)```", re.DOTALL)


def _iter_balanced_objects(text: str) -> Iterable[str]:
    """Yield top-level {...} spans, ignoring braces inside strings."""
    depth = 0
    start = -1
    in_str = False
    escape = False
    quote = ""
    for i, ch in enumerate(text):
        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote:
                in_str = False
            continue
        if ch in "\"'":
            in_str, quote = True, ch
        elif ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            if depth:
                depth -= 1
                if depth == 0 and start >= 0:
                    yield text[start : i + 1]
                    start = -1


_MARKERS = ("outcome", "steps", "friction_points", "in_character_summary", "analyst_summary")


def _score_candidate(obj: Any) -> int:
    if not isinstance(obj, dict):
        return -1
    return sum(1 for key in _MARKERS if key in obj)


def extract_report(text: str) -> dict[str, Any] | None:
    """Find the report object in a pile of agent output.

    Prefers the last fenced ```json block that looks like a report; falls back to
    any balanced object in the raw text. Returns None when nothing qualifies.
    """
    candidates: list[tuple[int, int, dict]] = []  # (score, position, obj)

    for match in _FENCE_RE.finditer(text):
        body = match.group(1).strip()
        try:
            obj = json.loads(body)
        except json.JSONDecodeError:
            # a fenced block may itself contain a nested object worth trying
            for span in _iter_balanced_objects(body):
                try:
                    obj = json.loads(span)
                except json.JSONDecodeError:
                    continue
                candidates.append((_score_candidate(obj), match.start(), obj))
            continue
        candidates.append((_score_candidate(obj), match.start(), obj))

    if not any(score > 0 for score, _, _ in candidates):
        for span in _iter_balanced_objects(text):
            if len(span) < 40:
                continue
            try:
                obj = json.loads(span)
            except json.JSONDecodeError:
                continue
            candidates.append((_score_candidate(obj), text.find(span), obj))

    scored = [c for c in candidates if c[0] > 0]
    if not scored:
        return None
    best = max(scored, key=lambda c: (c[0], c[1]))  # best match, latest wins ties
    return best[2]


# --------------------------------------------------------------------------
# result-text extractors per output format
# --------------------------------------------------------------------------


def _extract_plain(stdout: str) -> tuple[str, dict[str, Any]]:
    return stdout, {}


def _extract_claude_json(stdout: str) -> tuple[str, dict[str, Any]]:
    """`claude -p --output-format json` prints one envelope object."""
    obj = None
    for span in _iter_balanced_objects(stdout):
        try:
            candidate = json.loads(span)
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, dict) and "result" in candidate:
            obj = candidate
    if obj is None:
        return stdout, {}
    meta = {
        k: obj[k]
        for k in ("total_cost_usd", "duration_ms", "num_turns", "session_id", "subtype", "is_error")
        if k in obj
    }
    result = obj.get("result")
    return (result if isinstance(result, str) else json.dumps(result)), meta


def _event_texts(event: dict[str, Any]) -> list[str]:
    """Pull every piece of assistant prose out of one streamed event.

    This has to work on a *truncated* stream: when a session is killed mid-run the
    final result envelope never arrives, and the assistant messages are all the
    evidence left. Reading only the envelope would throw that away.
    """
    out: list[str] = []

    if event.get("type") == "result" and isinstance(event.get("result"), str):
        return [event["result"]]

    # claude stream-json: {"type":"assistant","message":{"content":[{"type":"text",...}]}}
    message = event.get("message")
    if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            out.append(content)
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and isinstance(block.get("text"), str) \
                        and block["text"].strip():
                    out.append(block["text"])

    # codex exec --json: {"type":"item.completed","item":{"type":"agent_message","text":...}}
    item = event.get("item")
    if isinstance(item, dict):
        for key in ("text", "content"):
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                out.append(value)
                break

    for key in ("text", "delta"):
        value = event.get(key)
        if isinstance(value, str) and value.strip():
            out.append(value)
            break

    return out


def _extract_ndjson(stdout: str) -> tuple[str, dict[str, Any]]:
    """Best-effort flatten of a JSONL event stream (codex --json, claude stream-json)."""
    chunks: list[str] = []
    meta: dict[str, Any] = {}
    for line in stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        for key in ("total_cost_usd", "duration_ms", "num_turns", "session_id", "usage"):
            if key in event:
                meta[key] = event[key]
        chunks.extend(_event_texts(event))
    return ("\n".join(chunks) if chunks else stdout), meta


# --------------------------------------------------------------------------
# backend registry
# --------------------------------------------------------------------------


def _brief(value: Any, limit: int = 70) -> str:
    text = " ".join(str(value).split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


def format_stream_event(line: str) -> str | None:
    """Turn one claude stream-json line into a short progress line, or None to skip.

    Without this, --echo on a streaming backend prints raw JSON and is unreadable;
    with it you can watch the session work in real time.
    """
    line = line.strip()
    if not line.startswith("{"):
        return None
    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        return None
    kind = event.get("type")

    if kind == "system" and event.get("subtype") == "init":
        return f"session {str(event.get('session_id', ''))[:8]} started"
    if kind == "result":
        cost = event.get("total_cost_usd")
        turns = event.get("num_turns")
        bits = [b for b in (f"{turns} turns" if turns else "",
                            f"${cost:.2f}" if isinstance(cost, (int, float)) else "") if b]
        return "finished" + (f" ({', '.join(bits)})" if bits else "")
    if kind != "assistant":
        return None

    parts: list[str] = []
    for block in (event.get("message") or {}).get("content") or []:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "text" and block.get("text", "").strip():
            parts.append(_brief(block["text"]))
        elif block.get("type") == "tool_use":
            data = block.get("input") or {}
            hint = (data.get("command") or data.get("file_path") or data.get("pattern")
                    or data.get("url") or data.get("prompt") or "")
            parts.append(f"→ {block.get('name', 'tool')}({_brief(hint, 50)})" if hint
                         else f"→ {block.get('name', 'tool')}")
    return " ".join(parts) or None


@dataclass
class AgentBackend:
    name: str
    exe: str
    base_args: list[str] = field(default_factory=list)
    prompt_mode: str = "stdin"  # "stdin" | "arg"
    prompt_arg_template: list[str] = field(default_factory=list)  # used when prompt_mode == "arg"
    stdin_args: list[str] = field(default_factory=list)  # extra args when piping the prompt
    model_flag: str = "--model"
    yolo_args: list[str] = field(default_factory=list)
    safe_args: list[str] = field(default_factory=list)
    cwd_flag: str = ""
    extractor: Callable[[str], tuple[str, dict]] = _extract_plain
    echo_formatter: Callable[[str], str | None] | None = None
    notes: str = ""

    def resolve_exe(self) -> str:
        found = shutil.which(self.exe)
        if not found:
            if self.name.startswith("custom"):
                raise AgentError(f"'{self.exe}' from --cmd was not found on PATH.")
            raise AgentError(
                f"'{self.exe}' was not found on PATH. Install the {self.name} CLI, "
                f"or use --agent custom --cmd \"your-cli --flags {PROMPT_TOKEN}\"."
            )
        return found

    def build(
        self,
        prompt: str,
        *,
        model: str = "",
        yolo: bool = False,
        cwd: str = "",
        extra_args: list[str] | None = None,
    ) -> tuple[list[str], str | None]:
        argv = [self.resolve_exe(), *self.base_args]
        if model and self.model_flag:
            argv += [self.model_flag, model]
        argv += self.yolo_args if yolo else self.safe_args
        if cwd and self.cwd_flag:
            argv += [self.cwd_flag, cwd]
        argv += list(extra_args or [])

        if self.prompt_mode == "arg":
            tail = [a.replace(PROMPT_TOKEN, prompt) for a in (self.prompt_arg_template or [PROMPT_TOKEN])]
            return argv + tail, None
        return argv + list(self.stdin_args), prompt


BACKENDS: dict[str, AgentBackend] = {
    "claude": AgentBackend(
        name="Claude Code",
        exe="claude",
        # streaming, not --output-format json: a buffered run that gets killed on timeout
        # writes a zero-byte log and the whole session is lost. Streaming survives the kill.
        base_args=["-p", "--output-format", "stream-json", "--verbose"],
        prompt_mode="stdin",
        model_flag="--model",
        safe_args=["--permission-mode", "acceptEdits"],
        yolo_args=["--dangerously-skip-permissions"],
        cwd_flag="--add-dir",
        extractor=_extract_ndjson,
        echo_formatter=format_stream_event,
        notes="Browser work needs the claude-in-chrome extension or a Playwright MCP server. "
              "Pass --yolo for unattended runs, or pre-allow tools in settings.json.",
    ),
    "claude-buffered": AgentBackend(
        name="Claude Code (buffered, one JSON envelope)",
        exe="claude",
        base_args=["-p", "--output-format", "json"],
        prompt_mode="stdin",
        model_flag="--model",
        safe_args=["--permission-mode", "acceptEdits"],
        yolo_args=["--dangerously-skip-permissions"],
        cwd_flag="--add-dir",
        extractor=_extract_claude_json,
        notes="Emits nothing until it exits, so a timeout loses the entire transcript. "
              "Only worth using if something downstream needs the single-envelope format.",
    ),
    "claude-text": AgentBackend(
        name="Claude Code (plain text output)",
        exe="claude",
        base_args=["-p"],
        prompt_mode="stdin",
        safe_args=["--permission-mode", "acceptEdits"],
        yolo_args=["--dangerously-skip-permissions"],
        cwd_flag="--add-dir",
        extractor=_extract_plain,
    ),
    "codex": AgentBackend(
        name="OpenAI Codex CLI",
        exe="codex",
        base_args=["exec"],
        prompt_mode="stdin",
        stdin_args=["-"],
        model_flag="-m",
        safe_args=["--full-auto"],
        yolo_args=["--dangerously-bypass-approvals-and-sandbox"],
        cwd_flag="--cd",
        extractor=_extract_plain,
        notes="Sandboxed by default; browser MCP servers must be configured in ~/.codex/config.toml.",
    ),
    "codex-json": AgentBackend(
        name="OpenAI Codex CLI (jsonl events)",
        exe="codex",
        base_args=["exec", "--json"],
        prompt_mode="stdin",
        stdin_args=["-"],
        model_flag="-m",
        safe_args=["--full-auto"],
        yolo_args=["--dangerously-bypass-approvals-and-sandbox"],
        cwd_flag="--cd",
        extractor=_extract_ndjson,
    ),
    "gemini": AgentBackend(
        name="Gemini CLI",
        exe="gemini",
        base_args=[],
        prompt_mode="arg",
        prompt_arg_template=["-p", PROMPT_TOKEN],
        model_flag="-m",
        yolo_args=["--yolo"],
        extractor=_extract_plain,
    ),
    "cursor": AgentBackend(
        name="Cursor Agent CLI",
        exe="cursor-agent",
        base_args=["--output-format", "text"],
        prompt_mode="arg",
        prompt_arg_template=["-p", PROMPT_TOKEN],
        model_flag="-m",
        yolo_args=["--force"],
        extractor=_extract_plain,
    ),
    "opencode": AgentBackend(
        name="OpenCode",
        exe="opencode",
        base_args=["run"],
        prompt_mode="arg",
        prompt_arg_template=[PROMPT_TOKEN],
        model_flag="-m",
        extractor=_extract_plain,
    ),
    "amp": AgentBackend(
        name="Amp",
        exe="amp",
        base_args=[],
        prompt_mode="stdin",
        stdin_args=["-x"],
        model_flag="",
        extractor=_extract_plain,
    ),
}


def make_custom_backend(command: str) -> AgentBackend:
    """Build a backend from a raw command template.

    Include `{prompt}` to pass the prompt as an argument; omit it and the prompt
    is piped to stdin instead.
    """
    parts = shlex.split(command, posix=(os.name != "nt"))
    if not parts:
        raise AgentError("--cmd was empty")
    exe, rest = parts[0], parts[1:]
    uses_arg = any(PROMPT_TOKEN in part for part in parts)
    return AgentBackend(
        name=f"custom ({exe})",
        exe=exe,
        base_args=[] if uses_arg else rest,
        prompt_mode="arg" if uses_arg else "stdin",
        prompt_arg_template=rest if uses_arg else [],
        model_flag="",
        extractor=_extract_plain,
    )


def get_backend(name: str, custom_cmd: str = "") -> AgentBackend:
    key = (name or "").strip().lower()
    key = {"claude-stream": "claude", "claude-json": "claude-buffered"}.get(key, key)
    if key in ("custom", "cmd"):
        if not custom_cmd:
            raise AgentError("--agent custom requires --cmd \"your-cli ...\"")
        return make_custom_backend(custom_cmd)
    if key not in BACKENDS:
        raise AgentError(
            f"Unknown agent '{name}'. Known: {', '.join(sorted(BACKENDS))}, custom."
        )
    return BACKENDS[key]


def available_backends() -> list[tuple[str, AgentBackend, bool]]:
    return [(key, be, shutil.which(be.exe) is not None) for key, be in sorted(BACKENDS.items())]


# --------------------------------------------------------------------------
# invocation
# --------------------------------------------------------------------------


@dataclass
class Invocation:
    argv: list[str]
    stdout: str
    stderr: str
    exit_code: int | None
    duration_s: float
    timed_out: bool
    text: str  # assistant text after extraction
    meta: dict[str, Any]


def _pump(stream, sink: list[str], log_handle, echo_prefix: str | None, formatter=None) -> None:
    try:
        for line in iter(stream.readline, ""):
            sink.append(line)
            if log_handle:
                log_handle.write(line)
                log_handle.flush()
            if echo_prefix is None:
                continue
            shown = formatter(line) if formatter else line.rstrip()
            if shown:
                sys.stderr.write(f"{echo_prefix}{shown}\n")
                sys.stderr.flush()
    except (ValueError, OSError):
        pass
    finally:
        try:
            stream.close()
        except Exception:
            pass


def run_agent(
    backend: AgentBackend,
    prompt: str,
    *,
    model: str = "",
    yolo: bool = False,
    cwd: str = "",
    extra_args: list[str] | None = None,
    timeout: int = 900,
    stdout_log: str = "",
    stderr_log: str = "",
    echo: bool = False,
    echo_prefix: str = "  | ",
    env: dict[str, str] | None = None,
) -> Invocation:
    """Run the CLI once, streaming its output to disk, and return what it said."""
    argv, stdin_payload = backend.build(
        prompt, model=model, yolo=yolo, cwd=cwd, extra_args=extra_args
    )

    proc_env = dict(os.environ)
    proc_env.setdefault("PYTHONIOENCODING", "utf-8")
    proc_env.setdefault("NO_COLOR", "1")
    proc_env.setdefault("FORCE_COLOR", "0")
    if env:
        proc_env.update(env)

    started = time.monotonic()
    creationflags = 0
    if os.name == "nt":
        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)

    proc = subprocess.Popen(
        argv,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        cwd=cwd or None,
        env=proc_env,
        creationflags=creationflags,
    )

    out_lines: list[str] = []
    err_lines: list[str] = []
    out_fh = open(stdout_log, "w", encoding="utf-8") if stdout_log else None
    err_fh = open(stderr_log, "w", encoding="utf-8") if stderr_log else None

    threads = [
        threading.Thread(
            target=_pump,
            args=(proc.stdout, out_lines, out_fh, echo_prefix if echo else None,
                  backend.echo_formatter),
            daemon=True,
        ),
        threading.Thread(target=_pump, args=(proc.stderr, err_lines, err_fh, None), daemon=True),
    ]
    for thread in threads:
        thread.start()

    timed_out = False
    try:
        if stdin_payload is not None:
            try:
                proc.stdin.write(stdin_payload)
            finally:
                try:
                    proc.stdin.close()
                except Exception:
                    pass
        elif proc.stdin:
            proc.stdin.close()
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        proc.kill()
        try:
            proc.wait(timeout=15)
        except Exception:
            pass
    except KeyboardInterrupt:
        proc.kill()
        raise
    finally:
        for thread in threads:
            thread.join(timeout=10)
        for handle in (out_fh, err_fh):
            if handle:
                handle.close()

    stdout = "".join(out_lines)
    stderr = "".join(err_lines)
    text, meta = backend.extractor(stdout)
    if not (text or "").strip():
        text = stdout
    return Invocation(
        argv=argv,
        stdout=stdout,
        stderr=stderr,
        exit_code=proc.returncode,
        duration_s=time.monotonic() - started,
        timed_out=timed_out,
        text=text,
        meta=meta,
    )
