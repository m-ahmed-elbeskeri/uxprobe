"""Core data structures for uxprobe: personas, tasks, run specs and reports."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass, field
from typing import Any

# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------


def slugify(value: str, max_len: int = 48) -> str:
    value = unicodedata.normalize("NFKD", str(value))
    value = value.encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return (value or "item")[:max_len].strip("-")


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [line.strip() for line in value.splitlines() if line.strip()]
    if isinstance(value, (list, tuple)):
        return [str(v).strip() for v in value if str(v).strip()]
    return [str(value)]


def _bullets(items: list[str], indent: str = "  ") -> str:
    return "\n".join(f"{indent}- {item}" for item in items)


def _filter_known(cls: type, data: dict[str, Any]) -> dict[str, Any]:
    """Drop unknown keys so hand-written YAML with typos degrades gracefully."""
    known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
    return {k: v for k, v in data.items() if k in known}


# --------------------------------------------------------------------------
# persona
# --------------------------------------------------------------------------


@dataclass
class Persona:
    """Who is sitting in front of the screen."""

    id: str
    name: str
    blurb: str = ""
    age: str = ""
    occupation: str = ""
    tech_savvy: str = "medium"  # low | medium | high
    device: str = "desktop"  # desktop | laptop | phone | tablet
    viewport: str = ""  # e.g. "390x844"; blank = agent's default
    patience: str = "medium"  # low | medium | high
    mood: str = "neutral"  # starting emotional baseline
    domain_knowledge: str = ""  # what they already know about this product space
    accessibility: list[str] = field(default_factory=list)
    goals: list[str] = field(default_factory=list)
    frustrations: list[str] = field(default_factory=list)
    habits: list[str] = field(default_factory=list)
    voice: str = ""  # how they talk when thinking aloud
    context: str = ""  # situation / why they're here right now

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Persona":
        data = dict(data)
        for key in ("accessibility", "goals", "frustrations", "habits"):
            if key in data:
                data[key] = _as_list(data[key])
        if "id" not in data and "name" in data:
            data["id"] = slugify(data["name"])
        if "name" not in data and "id" in data:
            data["name"] = str(data["id"]).replace("-", " ").title()
        return cls(**_filter_known(cls, data))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def prompt_block(self) -> str:
        lines = [f"NAME: {self.name}"]
        if self.age:
            lines.append(f"AGE: {self.age}")
        if self.occupation:
            lines.append(f"OCCUPATION: {self.occupation}")
        if self.blurb:
            lines.append(f"WHO THEY ARE: {self.blurb}")
        lines.append(f"TECH CONFIDENCE: {self.tech_savvy}")
        lines.append(f"DEVICE: {self.device}" + (f" ({self.viewport})" if self.viewport else ""))
        lines.append(f"PATIENCE FOR FRICTION: {self.patience}")
        lines.append(f"MOOD WHEN THEY ARRIVE: {self.mood}")
        if self.domain_knowledge:
            lines.append(f"PRIOR KNOWLEDGE: {self.domain_knowledge}")
        if self.context:
            lines.append(f"SITUATION RIGHT NOW: {self.context}")
        if self.goals:
            lines.append("WHAT THEY WANT:\n" + _bullets(self.goals))
        if self.frustrations:
            lines.append("WHAT MAKES THEM BAIL:\n" + _bullets(self.frustrations))
        if self.habits:
            lines.append("HABITS / EXPECTATIONS:\n" + _bullets(self.habits))
        if self.accessibility:
            lines.append("ACCESSIBILITY NEEDS:\n" + _bullets(self.accessibility))
        if self.voice:
            lines.append(f"HOW THEY TALK TO THEMSELVES: {self.voice}")
        return "\n".join(lines)


# --------------------------------------------------------------------------
# task
# --------------------------------------------------------------------------

DEFAULT_GUARDRAILS = [
    "Do not complete any purchase, payment, subscription or checkout with real payment details.",
    "Do not enter real personal data (real name, real email, real phone, real address). "
    "If a form needs data, use obviously fake test values and say so in the log.",
    "Do not delete, publish, send, or otherwise perform irreversible actions on someone's account or data. "
    "Walk up to the button, describe what you expect to happen, and stop.",
    "Do not attempt to bypass login walls, paywalls, captchas or rate limits.",
    "Stay on the target site and its own subdomains unless the task says otherwise.",
]


@dataclass
class Task:
    """What the persona is trying to get done."""

    id: str
    title: str
    goal: str
    url: str = ""
    success_criteria: list[str] = field(default_factory=list)
    starting_context: str = ""  # what they were told / where they came from
    constraints: list[str] = field(default_factory=list)
    guardrails: list[str] = field(default_factory=lambda: list(DEFAULT_GUARDRAILS))
    max_steps: int = 25
    notes: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Task":
        data = dict(data)
        for key in ("success_criteria", "constraints", "guardrails"):
            if key in data:
                data[key] = _as_list(data[key])
        if "goal" not in data:
            data["goal"] = data.get("title", "")
        if "title" not in data:
            data["title"] = (data.get("goal", "") or "task")[:60]
        if "id" not in data:
            data["id"] = slugify(data["title"])
        if "guardrails" not in data:
            data["guardrails"] = list(DEFAULT_GUARDRAILS)
        return cls(**_filter_known(cls, data))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def prompt_block(self) -> str:
        lines = [f"TASK: {self.title}", f"GOAL IN PLAIN WORDS: {self.goal}"]
        if self.url:
            lines.append(f"START AT: {self.url}")
        if self.starting_context:
            lines.append(f"HOW THEY GOT HERE: {self.starting_context}")
        if self.success_criteria:
            lines.append("THE TASK IS DONE WHEN:\n" + _bullets(self.success_criteria))
        if self.constraints:
            lines.append("CONSTRAINTS:\n" + _bullets(self.constraints))
        if self.notes:
            lines.append(f"NOTES: {self.notes}")
        lines.append(f"EFFORT BUDGET: give up after about {self.max_steps} interactions "
                     "and report it as an abandonment (that is a valid, useful result).")
        return "\n".join(lines)


# --------------------------------------------------------------------------
# run spec + result
# --------------------------------------------------------------------------


@dataclass
class RunSpec:
    """One persona x task x attempt, plus how to invoke the agent."""

    persona: Persona
    task: Task
    agent: str = "claude"
    model: str = ""
    attempt: int = 1
    browser: str = "auto"
    timeout: int = 900
    yolo: bool = False
    extra_args: list[str] = field(default_factory=list)
    cwd: str = ""
    screenshots: bool = True

    @property
    def run_id(self) -> str:
        base = f"{self.persona.id}__{self.task.id}"
        return f"{base}__try{self.attempt}" if self.attempt > 1 else base

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["run_id"] = self.run_id
        return data


@dataclass
class RunResult:
    """Everything we learned from one run."""

    spec: RunSpec
    run_dir: str
    ok: bool
    report: dict[str, Any] = field(default_factory=dict)
    error: str = ""
    started_at: str = ""
    finished_at: str = ""
    duration_s: float = 0.0
    exit_code: int | None = None
    agent_meta: dict[str, Any] = field(default_factory=dict)
    raw_output_chars: int = 0
    truncated: bool = False  # session was cut short; report reconstructed from a partial transcript

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.spec.run_id,
            "truncated": self.truncated,
            "persona": self.spec.persona.to_dict(),
            "task": self.spec.task.to_dict(),
            "agent": self.spec.agent,
            "model": self.spec.model,
            "attempt": self.spec.attempt,
            "run_dir": self.run_dir,
            "ok": self.ok,
            "error": self.error,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_s": round(self.duration_s, 2),
            "exit_code": self.exit_code,
            "agent_meta": self.agent_meta,
            "raw_output_chars": self.raw_output_chars,
            "report": self.report,
        }


# --------------------------------------------------------------------------
# report normalisation
# --------------------------------------------------------------------------

SEVERITIES = ("blocker", "major", "minor", "nitpick")
OUTCOMES = ("completed", "partial", "failed", "abandoned")


def _clamp_int(value: Any, lo: int, hi: int, default: int | None = None) -> int | None:
    try:
        n = int(round(float(value)))
    except (TypeError, ValueError):
        return default
    return max(lo, min(hi, n))


def normalize_report(raw: Any) -> dict[str, Any]:
    """Coerce whatever the model emitted into the shape the reporters expect.

    Models drift on enum spelling and on list-vs-string, so every field here is
    forgiving; nothing raises. Missing fields come back as empty, not absent.
    """
    data = raw if isinstance(raw, dict) else {}
    out: dict[str, Any] = {}

    outcome = str(data.get("outcome", data.get("task_completed", ""))).strip().lower()
    if outcome in ("true", "yes", "success", "done"):
        outcome = "completed"
    elif outcome in ("false", "no"):
        outcome = "failed"
    elif outcome in ("gave up", "gave_up", "quit", "bailed"):
        outcome = "abandoned"
    out["outcome"] = outcome if outcome in OUTCOMES else "unknown"

    out["difficulty"] = _clamp_int(data.get("difficulty"), 1, 5)
    out["confidence"] = _clamp_int(data.get("confidence"), 1, 5)
    out["ease_score"] = _clamp_int(data.get("ease_score", data.get("sus_score")), 0, 100)
    out["would_return"] = data.get("would_return")
    out["would_recommend"] = data.get("would_recommend")
    out["emotional_arc"] = str(data.get("emotional_arc", "") or "")
    out["first_impression"] = str(data.get("first_impression", "") or "")
    out["in_character_summary"] = str(
        data.get("in_character_summary", data.get("verbatim_summary", "")) or ""
    )
    out["analyst_summary"] = str(data.get("analyst_summary", data.get("summary", "")) or "")
    out["one_thing_to_fix"] = str(data.get("one_thing_to_fix", "") or "")

    steps = []
    for i, step in enumerate(data.get("steps") or [], start=1):
        if not isinstance(step, dict):
            step = {"what_happened": str(step)}
        steps.append(
            {
                "n": _clamp_int(step.get("n"), 1, 10_000, i) or i,
                "intent": str(step.get("intent", "") or ""),
                "action": str(step.get("action", "") or ""),
                "expected": str(step.get("expected", step.get("expectation", "")) or ""),
                "what_happened": str(step.get("what_happened", step.get("result", "")) or ""),
                "thought": str(step.get("thought", step.get("quote", "")) or ""),
                "feeling": str(step.get("feeling", "") or ""),
                "friction": _clamp_int(step.get("friction"), 0, 3, 0) or 0,
                "seconds": step.get("seconds"),
                "screenshot": str(step.get("screenshot", "") or ""),
            }
        )
    out["steps"] = steps

    findings = []
    for item in data.get("friction_points") or data.get("findings") or []:
        if not isinstance(item, dict):
            item = {"what": str(item)}
        sev = str(item.get("severity", "minor")).strip().lower()
        if sev in ("critical", "showstopper", "severe", "high"):
            sev = "blocker"
        elif sev in ("medium", "moderate"):
            sev = "major"
        elif sev in ("low", "trivial", "cosmetic", "polish"):
            sev = "nitpick"
        findings.append(
            {
                "severity": sev if sev in SEVERITIES else "minor",
                "where": str(item.get("where", item.get("location", "")) or ""),
                "what": str(item.get("what", item.get("issue", item.get("title", ""))) or ""),
                "why_it_hurts": str(item.get("why_it_hurts", item.get("impact", "")) or ""),
                "evidence": str(item.get("evidence", "") or ""),
                "suggested_fix": str(item.get("suggested_fix", item.get("fix", "")) or ""),
                "heuristic": str(item.get("heuristic", "") or ""),
            }
        )
    order = {s: i for i, s in enumerate(SEVERITIES)}
    findings.sort(key=lambda f: order.get(f["severity"], 99))
    out["friction_points"] = findings

    out["delights"] = _as_list(data.get("delights"))
    out["confusions"] = _as_list(data.get("confusions", data.get("confusion_moments")))
    out["unmet_expectations"] = _as_list(data.get("unmet_expectations"))
    out["accessibility_notes"] = _as_list(data.get("accessibility_notes"))
    out["questions_for_the_team"] = _as_list(data.get("questions_for_the_team"))
    out["tags"] = _as_list(data.get("tags"))
    out["pages_visited"] = _as_list(data.get("pages_visited"))
    out["technical_observations"] = _as_list(data.get("technical_observations"))

    # keep anything the model volunteered that we didn't model
    extras = {k: v for k, v in data.items() if k not in out and k not in
              ("task_completed", "verbatim_summary", "summary", "findings",
               "confusion_moments", "sus_score", "expectation", "result", "quote")}
    if extras:
        out["extra"] = extras
    return out


def severity_counts(report: dict[str, Any]) -> dict[str, int]:
    counts = {s: 0 for s in SEVERITIES}
    for finding in report.get("friction_points", []):
        sev = finding.get("severity", "minor")
        if sev in counts:
            counts[sev] += 1
    return counts
