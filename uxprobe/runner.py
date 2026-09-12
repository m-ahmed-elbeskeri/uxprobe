"""Orchestration: turn RunSpecs into RunResults on disk."""

from __future__ import annotations

import json
import os
import shutil
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Callable

from .agents import AgentError, Invocation, extract_report, get_backend, run_agent
from .models import RunResult, RunSpec, normalize_report, severity_counts, slugify
from .prompts import build_prompt, build_repair_prompt
from .reporting import (
    render_index_html,
    render_index_markdown,
    render_run_markdown,
    write_findings_csv,
    write_summary_json,
    write_tickets_markdown,
)

_print_lock = threading.Lock()


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def say(message: str) -> None:
    with _print_lock:
        print(message, flush=True)


def make_out_dir(root: str, study_name: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = os.path.join(root, f"{stamp}-{slugify(study_name)}")
    os.makedirs(path, exist_ok=True)
    return path


class JsonlLog:
    """Append-only event log, safe across worker threads."""

    def __init__(self, path: str):
        self.path = path
        self._lock = threading.Lock()

    def write(self, event: str, **fields) -> None:
        record = {"ts": _now(), "event": event, **fields}
        line = json.dumps(record, ensure_ascii=False, default=str)
        with self._lock:
            with open(self.path, "a", encoding="utf-8") as handle:
                handle.write(line + "\n")


def execute_run(
    spec: RunSpec,
    out_dir: str,
    *,
    custom_cmd: str = "",
    echo: bool = False,
    repair_attempts: int = 1,
    log: JsonlLog | None = None,
    dry_run: bool = False,
) -> RunResult:
    """Run one persona/task session end to end and write its artefacts."""
    run_dir = os.path.join(out_dir, spec.run_id)
    os.makedirs(run_dir, exist_ok=True)
    started_wall = time.monotonic()
    started_at = _now()

    prompt = build_prompt(spec)
    prompt += (
        "\n\n=== WHERE TO PUT FILES ===\n"
        f"Work inside this directory and nothing outside it:\n  {run_dir}\n"
        "  - Screenshots, downloads and exports go directly in it, they are the evidence.\n"
        f"  - Anything disposable (browser profiles, user-data-dir, node_modules, temp "
        f"downloads) goes in {os.path.join(run_dir, '_scratch')}, which is deleted when the "
        "session ends. A browser profile left in the run directory is tens of megabytes of "
        "rubbish per session, so always point --user-data-dir at _scratch.\n"
    )
    with open(os.path.join(run_dir, "prompt.txt"), "w", encoding="utf-8") as handle:
        handle.write(prompt)
    with open(os.path.join(run_dir, "spec.json"), "w", encoding="utf-8") as handle:
        json.dump(spec.to_dict(), handle, indent=2, ensure_ascii=False)

    result = RunResult(spec=spec, run_dir=run_dir, ok=False, started_at=started_at)

    if dry_run:
        result.ok = True
        result.error = "dry run - agent not invoked"
        result.finished_at = _now()
        say(f"  [dry-run] {spec.run_id}: prompt written to {run_dir}\\prompt.txt")
        return result

    if log:
        log.write("run_start", run_id=spec.run_id, persona=spec.persona.id,
                  task=spec.task.id, agent=spec.agent)

    try:
        backend = get_backend(spec.agent, custom_cmd)
    except AgentError as exc:
        result.error = str(exc)
        result.finished_at = _now()
        result.duration_s = time.monotonic() - started_wall
        _write_run_artifacts(result)
        return result

    say(f"▶ {spec.persona.name} → {spec.task.title}  ({spec.agent})")

    invocation: Invocation | None = None
    try:
        invocation = run_agent(
            backend,
            prompt,
            model=spec.model,
            yolo=spec.yolo,
            cwd=spec.cwd or "",
            extra_args=spec.extra_args,
            timeout=spec.timeout,
            stdout_log=os.path.join(run_dir, "stdout.log"),
            stderr_log=os.path.join(run_dir, "stderr.log"),
            echo=echo,
            echo_prefix=f"  {spec.persona.id[:12]:>12} | ",
        )
    except AgentError as exc:
        result.error = str(exc)
    except Exception as exc:  # noqa: BLE001 - surfaced in the report, not swallowed
        result.error = f"{type(exc).__name__}: {exc}"

    if invocation is not None:
        result.exit_code = invocation.exit_code
        result.agent_meta = invocation.meta
        result.raw_output_chars = len(invocation.stdout)
        with open(os.path.join(run_dir, "agent_text.md"), "w", encoding="utf-8") as handle:
            handle.write(invocation.text or "")
        with open(os.path.join(run_dir, "argv.json"), "w", encoding="utf-8") as handle:
            json.dump(invocation.argv, handle, indent=2, ensure_ascii=False)

        if invocation.timed_out:
            result.error = f"agent timed out after {spec.timeout}s"
            result.truncated = True

        raw = extract_report(invocation.text) or extract_report(invocation.stdout)

        transcript = invocation.text or invocation.stdout
        if raw is None and result.truncated and len(transcript.strip()) < 200:
            say(f"  ⚠ {spec.run_id}: timed out with an empty transcript, nothing to salvage. "
                f"The '{spec.agent}' backend may be buffering; try --agent claude.")

        attempt = 0
        while raw is None and attempt < repair_attempts and len(transcript.strip()) >= 200:
            attempt += 1
            say(f"  ... {spec.run_id}: "
                + ("session cut short, salvaging a report from the partial transcript"
                   if result.truncated else "no JSON report, asking to reformat")
                + f" (attempt {attempt})")
            try:
                repair = run_agent(
                    backend,
                    build_repair_prompt(transcript, truncated=result.truncated),
                    model=spec.model,
                    yolo=spec.yolo,
                    cwd=spec.cwd or "",
                    extra_args=spec.extra_args,
                    timeout=min(spec.timeout, 300),
                    stdout_log=os.path.join(run_dir, f"repair{attempt}.log"),
                    echo=False,
                )
            except Exception as exc:  # noqa: BLE001
                result.error = result.error or f"repair failed: {exc}"
                break
            raw = extract_report(repair.text) or extract_report(repair.stdout)

        if raw is not None:
            result.report = normalize_report(raw)
            # A salvaged report is a usable result, not a failure, it just carries a caveat.
            result.ok = True
        else:
            result.error = result.error or (
                "the agent produced no parseable JSON report, see stdout.log"
            )
            if invocation.exit_code not in (0, None):
                result.error += f" (exit code {invocation.exit_code})"

    result.duration_s = time.monotonic() - started_wall
    result.finished_at = _now()
    _prune_scratch(run_dir)
    _write_run_artifacts(result)

    counts = severity_counts(result.report)
    outcome = result.report.get("outcome", "unknown") if result.ok else "no report"
    say(
        f"■ {spec.persona.name} → {spec.task.title}: {outcome}"
        f" · difficulty {result.report.get('difficulty', '-')}/5"
        f" · {counts['blocker']} blocker(s)"
        f" · {result.duration_s:.0f}s"
        + (f"  ⚠ {result.error}" if result.error else "")
    )
    if log:
        log.write("run_end", run_id=spec.run_id, ok=result.ok, outcome=outcome,
                  difficulty=result.report.get("difficulty"), blockers=counts["blocker"],
                  duration_s=round(result.duration_s, 1), error=result.error)
    return result


def _prune_scratch(run_dir: str) -> None:
    """Delete only the directory we explicitly told the agent was disposable."""
    scratch = os.path.join(run_dir, "_scratch")
    if os.path.isdir(scratch) and os.path.abspath(scratch).startswith(os.path.abspath(run_dir)):
        shutil.rmtree(scratch, ignore_errors=True)


def _write_run_artifacts(result: RunResult) -> None:
    with open(os.path.join(result.run_dir, "report.json"), "w", encoding="utf-8") as handle:
        json.dump(result.to_dict(), handle, indent=2, ensure_ascii=False)
    with open(os.path.join(result.run_dir, "report.md"), "w", encoding="utf-8") as handle:
        handle.write(render_run_markdown(result))


def load_existing(out_dir: str, run_id: str) -> RunResult | None:
    """Read a previously completed session back off disk, for --resume."""
    path = os.path.join(out_dir, run_id, "report.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None
    if not data.get("ok") or not (data.get("report") or {}).get("steps"):
        return None  # a failed attempt is worth retrying, not resuming
    from .models import Persona, Task  # local import keeps the module graph flat

    spec = RunSpec(
        persona=Persona.from_dict(data.get("persona", {})),
        task=Task.from_dict(data.get("task", {})),
        agent=data.get("agent", ""),
        model=data.get("model", ""),
        attempt=data.get("attempt", 1),
    )
    return RunResult(
        spec=spec, run_dir=os.path.join(out_dir, run_id), ok=True,
        report=data.get("report") or {}, error=data.get("error", ""),
        started_at=data.get("started_at", ""), finished_at=data.get("finished_at", ""),
        duration_s=float(data.get("duration_s") or 0), exit_code=data.get("exit_code"),
        agent_meta=data.get("agent_meta") or {}, truncated=bool(data.get("truncated")),
    )


def spent_so_far(results: list[RunResult]) -> float:
    total = 0.0
    for result in results:
        cost = result.agent_meta.get("total_cost_usd")
        if isinstance(cost, (int, float)):
            total += float(cost)
    return total


def execute_study(
    specs: list[RunSpec],
    out_dir: str,
    study_name: str,
    *,
    custom_cmd: str = "",
    concurrency: int = 1,
    echo: bool = False,
    repair_attempts: int = 1,
    dry_run: bool = False,
    resume: bool = False,
    max_cost: float = 0.0,
    on_result: Callable[[RunResult], None] | None = None,
) -> list[RunResult]:
    """Run every spec, then write the study-level reports."""
    log = JsonlLog(os.path.join(out_dir, "events.jsonl"))

    order = {spec.run_id: i for i, spec in enumerate(specs)}  # before any filtering

    done: dict[str, RunResult] = {}
    if resume:
        for spec in specs:
            existing = load_existing(out_dir, spec.run_id)
            if existing is not None:
                done[spec.run_id] = existing
        if done:
            say(f"resuming: {len(done)} session(s) already complete, "
                f"{len(specs) - len(done)} to run")
        specs = [s for s in specs if s.run_id not in done]
    meta = {
        "study": study_name,
        "started_at": _now(),
        "sessions": len(specs),
        "concurrency": concurrency,
        "cli": " ".join(sys.argv[1:]),
    }
    log.write("study_start", **meta)

    results: list[RunResult] = list(done.values())
    skipped_for_budget = 0

    if concurrency <= 1:
        for spec in specs:
            if max_cost and spent_so_far(results) >= max_cost:
                skipped_for_budget += 1
                continue
            result = execute_run(spec, out_dir, custom_cmd=custom_cmd, echo=echo,
                                 repair_attempts=repair_attempts, log=log, dry_run=dry_run)
            results.append(result)
            if on_result:
                on_result(result)
    else:
        # the cap can only be enforced between waves, since costs land at session end
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            futures = {
                pool.submit(execute_run, spec, out_dir, custom_cmd=custom_cmd, echo=echo,
                            repair_attempts=repair_attempts, log=log, dry_run=dry_run): spec
                for spec in specs
            }
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                if on_result:
                    on_result(result)

    if skipped_for_budget:
        say(f"⚠ stopped early: --max-cost ${max_cost:.2f} reached, "
            f"{skipped_for_budget} session(s) not run")
        log.write("budget_stop", max_cost=max_cost, skipped=skipped_for_budget)

    results.sort(key=lambda r: order.get(r.spec.run_id, len(order)))

    meta["finished_at"] = _now()
    write_study_reports(results, out_dir, study_name, meta)
    log.write("study_end", ok=sum(1 for r in results if r.ok), total=len(results))
    return results


def write_study_reports(
    results: list[RunResult], out_dir: str, study_name: str, meta: dict
) -> None:
    with open(os.path.join(out_dir, "index.md"), "w", encoding="utf-8") as handle:
        handle.write(render_index_markdown(results, study_name, meta))
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as handle:
        handle.write(render_index_html(results, study_name, meta))
    write_findings_csv(results, os.path.join(out_dir, "issues.csv"))
    write_tickets_markdown(results, os.path.join(out_dir, "issues.md"), study_name)
    write_summary_json(results, os.path.join(out_dir, "summary.json"), meta)
