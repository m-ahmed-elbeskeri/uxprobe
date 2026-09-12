"""Loading study definitions from YAML or JSON files."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any

from .models import DEFAULT_GUARDRAILS, Persona, RunSpec, Task, _as_list
from .personas import BUILTIN_PERSONAS, get_persona

try:  # PyYAML is optional; JSON suites work without it
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None


class ConfigError(RuntimeError):
    pass


def load_data_file(path: str) -> Any:
    if not os.path.exists(path):
        raise ConfigError(f"No such file: {path}")
    with open(path, "r", encoding="utf-8") as handle:
        text = handle.read()
    if path.lower().endswith(".json"):
        return json.loads(text)
    if yaml is None:
        try:  # a JSON file with a .yaml name still works
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise ConfigError(
                f"{path} looks like YAML but PyYAML is not installed. "
                "Run `pip install pyyaml`, or write the study as .json."
            ) from exc
    return yaml.safe_load(text)


@dataclass
class Study:
    """A full study definition: personas x tasks x agents."""

    name: str = "study"
    description: str = ""
    base_url: str = ""
    personas: list[Persona] = field(default_factory=list)
    tasks: list[Task] = field(default_factory=list)
    agents: list[str] = field(default_factory=lambda: ["claude"])
    model: str = ""
    repeat: int = 1
    browser: str = "auto"
    timeout: int = 900
    yolo: bool = False
    screenshots: bool = True
    extra_args: list[str] = field(default_factory=list)
    guardrails: list[str] = field(default_factory=list)

    def expand(self) -> list[RunSpec]:
        specs: list[RunSpec] = []
        for agent in self.agents:
            for persona in self.personas:
                for task in self.tasks:
                    for attempt in range(1, max(1, self.repeat) + 1):
                        specs.append(
                            RunSpec(
                                persona=persona,
                                task=task,
                                agent=agent,
                                model=self.model,
                                attempt=attempt,
                                browser=self.browser,
                                timeout=self.timeout,
                                yolo=self.yolo,
                                extra_args=list(self.extra_args),
                                screenshots=self.screenshots,
                            )
                        )
        return specs


def _resolve_persona(entry: Any, extra: dict[str, Persona]) -> Persona:
    if isinstance(entry, str):
        persona = extra.get(entry.strip().lower()) or get_persona(entry)
        if persona is None:
            known = ", ".join(sorted(set(BUILTIN_PERSONAS) | set(extra)))
            raise ConfigError(f"Unknown persona '{entry}'. Known: {known}")
        return persona
    if isinstance(entry, dict):
        if "extends" in entry:
            base = _resolve_persona(entry["extends"], extra)
            merged = base.to_dict()
            merged.update({k: v for k, v in entry.items() if k != "extends"})
            merged.setdefault("id", base.id + "-variant")
            return Persona.from_dict(merged)
        return Persona.from_dict(entry)
    raise ConfigError(f"Cannot read persona entry: {entry!r}")


def load_study(path: str) -> Study:
    data = load_data_file(path)
    if not isinstance(data, dict):
        raise ConfigError(f"{path} must contain a mapping at the top level")

    base_dir = os.path.dirname(os.path.abspath(path))

    # persona files referenced by the study
    extra: dict[str, Persona] = {}
    for ref in data.get("persona_files", []) or []:
        ref_path = ref if os.path.isabs(ref) else os.path.join(base_dir, ref)
        loaded = load_data_file(ref_path)
        entries = loaded.get("personas", loaded) if isinstance(loaded, dict) else loaded
        if isinstance(entries, dict):
            entries = [{"id": k, **v} for k, v in entries.items()]
        for entry in entries or []:
            persona = Persona.from_dict(entry)
            extra[persona.id] = persona

    # inline persona definitions may also be reused by id
    for entry in data.get("define_personas", []) or []:
        persona = Persona.from_dict(entry)
        extra[persona.id] = persona

    personas = [_resolve_persona(entry, extra) for entry in (data.get("personas") or [])]
    if not personas:
        raise ConfigError(f"{path} defines no personas")

    base_url = str(data.get("base_url", "") or "")
    shared_guardrails = data.get("guardrails")

    tasks: list[Task] = []
    for entry in data.get("tasks") or []:
        if isinstance(entry, str):
            entry = {"title": entry, "goal": entry}
        entry = dict(entry)
        if base_url and not entry.get("url"):
            entry["url"] = base_url
        # study-level guardrails add to the built-in safety defaults, they do not replace them
        if shared_guardrails and "guardrails" not in entry:
            entry["guardrails"] = list(DEFAULT_GUARDRAILS) + _as_list(shared_guardrails)
        for key in ("max_steps",):
            if key in data and key not in entry:
                entry[key] = data[key]
        tasks.append(Task.from_dict(entry))
    if not tasks:
        raise ConfigError(f"{path} defines no tasks")

    agents = data.get("agents") or [data.get("agent", "claude")]
    if isinstance(agents, str):
        agents = [agents]

    return Study(
        name=str(data.get("name", os.path.splitext(os.path.basename(path))[0])),
        description=str(data.get("description", "") or ""),
        base_url=base_url,
        personas=personas,
        tasks=tasks,
        agents=[str(a) for a in agents],
        model=str(data.get("model", "") or ""),
        repeat=int(data.get("repeat", 1) or 1),
        browser=str(data.get("browser", "auto") or "auto"),
        timeout=int(data.get("timeout", 900) or 900),
        yolo=bool(data.get("yolo", False)),
        screenshots=bool(data.get("screenshots", True)),
        extra_args=[str(a) for a in (data.get("extra_args") or [])],
        guardrails=[str(g) for g in (shared_guardrails or [])],
    )


EXAMPLE_STUDY = """\
# uxprobe study definition
name: checkout-review
description: Can four different people get through sign-up and checkout?
base_url: https://example.com

# Which CLI agents drive the browser. Each one runs every persona x task.
agents: [claude]
# model: claude-opus-5          # optional, passed through to the CLI
browser: auto                   # auto | chrome-mcp | playwright-mcp | playwright-script | none
timeout: 900                    # seconds per session
repeat: 1                       # run each combination N times to see variance
screenshots: true

# Built-in ids: first-timer, power-user, mobile-commuter, screen-reader,
# skeptical-buyer, impatient-returner, cautious-senior, distracted-multitasker,
# edge-case-hunter, non-native-speaker.  Run `uxprobe personas` to see them all.
personas:
  - first-timer
  - mobile-commuter
  - screen-reader
  # tweak a built-in without redefining it:
  - extends: power-user
    id: power-user-impatient
    patience: low
    context: Has 90 seconds between meetings.
  # or define one from scratch:
  - id: budget-parent
    name: Nadia, budgeting for the family
    occupation: Part-time pharmacist
    tech_savvy: medium
    device: phone
    patience: low
    goals:
      - Find the real total price including delivery before committing to anything
    frustrations:
      - Fees that only appear at the last step
      - Newsletter pop-ups over the content

tasks:
  - id: understand-product
    title: Work out what this company sells
    goal: Land on the homepage and decide, without signing up, whether this is for you.
    success_criteria:
      - Can state in one sentence what the product does and who it is for
      - Found pricing, or established that pricing is not published
    max_steps: 15

  - id: find-support
    title: Get help with a problem
    goal: You think you were charged twice. Find out how to reach a human about it.
    success_criteria:
      - Found a support route (chat, email, phone or form)
      - Know roughly how long a reply will take
    max_steps: 20

# Extra house rules on top of the built-in safety defaults.
guardrails:
  - Do not create a real account; stop at the final submit and describe what you expect.
  - Do not enter real card details anywhere, ever.
"""
