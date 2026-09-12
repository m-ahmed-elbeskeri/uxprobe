"""Rendering run results as Markdown, HTML and CSV."""

from __future__ import annotations

import csv
import html
import json
import os
import re
from typing import Any, Iterable

from .analysis import (
    BAND_BACKLOG,
    BAND_FIX_FIRST,
    BAND_NEXT,
    GRADE_BLURB,
    IMPRESSION,
    MEASURED,
    issue_ticket,
    prioritise,
    study_stats,
)
from .models import RunResult, SEVERITIES, severity_counts

SEV_EMOJI = {"blocker": "🛑", "major": "🔶", "minor": "🔹", "nitpick": "·"}
OUTCOME_EMOJI = {
    "completed": "✅",
    "partial": "🟡",
    "failed": "❌",
    "abandoned": "🚪",
    "unknown": "❔",
}
FEELING_EMOJI = {
    "confident": "😌", "confused": "😕", "annoyed": "😤", "delighted": "😄",
    "anxious": "😬", "bored": "🥱", "lost": "🤨", "relieved": "😮‍💨",
    "frustrated": "😠", "surprised": "😲", "impatient": "⏳", "neutral": "😐",
}


def _feel(word: str) -> str:
    key = (word or "").strip().lower().split(",")[0].split("/")[0].strip()
    return f"{FEELING_EMOJI.get(key, '')} {word}".strip() if word else ""


def _fmt(value: Any, dash: str = "-") -> str:
    if value is None or value == "":
        return dash
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value)


def _md_escape_cell(text: str) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ").strip()


# files uxprobe itself writes into a run directory, everything else came from the agent
_OWN_FILES = {"prompt.txt", "spec.json", "report.json", "report.md", "stdout.log",
              "stderr.log", "agent_text.md", "argv.json"}


def _human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} GB"


def _session_artifacts(run_dir: str, limit: int = 20) -> list[tuple[str, str]]:
    """Downloads, exports and scripts the agent left behind, often the best evidence."""
    try:
        names = sorted(os.listdir(run_dir))
    except OSError:
        return []
    out: list[tuple[str, str]] = []
    for name in names:
        path = os.path.join(run_dir, name)
        if not os.path.isfile(path) or name in _OWN_FILES:
            continue
        if name.lower().endswith(".png") or name.startswith("repair"):
            continue  # screenshots are shown inline; repair logs are plumbing
        out.append((name, _human_size(os.path.getsize(path))))
    return out[:limit]


# --------------------------------------------------------------------------
# per-run markdown
# --------------------------------------------------------------------------


def render_run_markdown(result: RunResult) -> str:
    spec = result.spec
    report = result.report or {}
    persona, task = spec.persona, spec.task
    counts = severity_counts(report)
    outcome = report.get("outcome", "unknown")

    out: list[str] = []
    add = out.append

    add(f"# {persona.name} → {task.title}")
    add("")
    add(
        f"**{OUTCOME_EMOJI.get(outcome, '❔')} {outcome}**  ·  "
        f"difficulty **{_fmt(report.get('difficulty'))}/5**  ·  "
        f"confidence **{_fmt(report.get('confidence'))}/5**  ·  "
        f"ease **{_fmt(report.get('ease_score'))}/100**"
    )
    add("")
    cost = result.agent_meta.get("total_cost_usd")
    turns = result.agent_meta.get("num_turns")
    add(
        f"<sub>agent `{spec.agent}`"
        + (f" · model `{spec.model}`" if spec.model else "")
        + f" · {result.duration_s / 60:.0f}m {result.duration_s % 60:.0f}s"
        + (f" · {turns} turns" if turns else "")
        + (f" · ${cost:.2f}" if isinstance(cost, (int, float)) else "")
        + (f" · attempt {spec.attempt}" if spec.attempt > 1 else "")
        + f" · started {result.started_at}</sub>"
    )
    add("")

    if not result.ok:
        add(f"> ⚠️ **Run problem:** {result.error or 'unknown error'}")
        add("")

    add("## Who and what")
    add("")
    add(f"- **Persona:** {persona.name}: {persona.blurb or persona.occupation or persona.id}")
    add(f"- **Device:** {persona.device}{f' ({persona.viewport})' if persona.viewport else ''}"
        f" · tech confidence {persona.tech_savvy} · patience {persona.patience}")
    add(f"- **Task:** {task.goal}")
    if task.url:
        add(f"- **Start URL:** {task.url}")
    add("")

    if report.get("first_impression"):
        add("## First impression")
        add("")
        add(f"> {report['first_impression']}")
        add("")

    if report.get("in_character_summary"):
        add("## In their words")
        add("")
        add(f"> {report['in_character_summary']}")
        add("")

    steps = report.get("steps") or []
    if steps:
        add("## What happened, step by step")
        add("")
        add("| # | Tried to | Did | Expected | Got | Felt | Friction |")
        add("|---:|---|---|---|---|---|:--:|")
        for step in steps:
            bar = "▰" * step.get("friction", 0) + "▱" * (3 - step.get("friction", 0))
            add(
                "| {n} | {intent} | {action} | {expected} | {got} | {feel} | {bar} |".format(
                    n=step.get("n", ""),
                    intent=_md_escape_cell(step.get("intent", "")),
                    action=_md_escape_cell(step.get("action", "")),
                    expected=_md_escape_cell(step.get("expected", "")),
                    got=_md_escape_cell(step.get("what_happened", "")),
                    feel=_md_escape_cell(_feel(step.get("feeling", ""))),
                    bar=bar,
                )
            )
        add("")
        thoughts = [s for s in steps if s.get("thought") or s.get("screenshot")]
        if thoughts:
            add("<details><summary>Thinking aloud, with screenshots</summary>")
            add("")
            for step in thoughts:
                if step.get("thought"):
                    add(f"**{step.get('n')}.** {step['thought']}")
                    add("")
                shot = step.get("screenshot", "")
                if shot and os.path.exists(os.path.join(result.run_dir, shot)):
                    caption = step.get("action") or step.get("what_happened") or shot
                    add(f"![Step {step.get('n')}: {_md_escape_cell(caption)}]({shot})")
                    add("")
            add("</details>")
            add("")

    findings = report.get("friction_points") or []
    if findings:
        add("## Friction")
        add("")
        add(
            "  ".join(
                f"{SEV_EMOJI[s]} {counts[s]} {s}" for s in SEVERITIES if counts[s]
            )
        )
        add("")
        for finding in findings:
            add(f"### {SEV_EMOJI.get(finding['severity'], '·')} {finding['severity'].upper()}, "
                f"{finding.get('what') or '(unnamed)'}")
            add("")
            if finding.get("where"):
                add(f"- **Where:** {finding['where']}")
            if finding.get("why_it_hurts"):
                add(f"- **Why it hurts:** {finding['why_it_hurts']}")
            if finding.get("evidence"):
                add(f"- **Evidence:** {finding['evidence']}")
            if finding.get("suggested_fix"):
                add(f"- **Suggested fix:** {finding['suggested_fix']}")
            if finding.get("heuristic"):
                add(f"- **Heuristic:** {finding['heuristic']}")
            add("")

    for title, key in (
        ("What worked", "delights"),
        ("Moments of confusion", "confusions"),
        ("Unmet expectations", "unmet_expectations"),
        ("Accessibility notes", "accessibility_notes"),
        ("Technical observations", "technical_observations"),
        ("Questions for the team", "questions_for_the_team"),
    ):
        items = report.get(key) or []
        if items:
            add(f"## {title}")
            add("")
            for item in items:
                add(f"- {item}")
            add("")

    if report.get("emotional_arc"):
        add("## Emotional arc")
        add("")
        add(report["emotional_arc"])
        add("")

    if report.get("one_thing_to_fix"):
        add("## If you fix one thing")
        add("")
        add(f"**{report['one_thing_to_fix']}**")
        add("")

    if report.get("analyst_summary"):
        add("## Analyst summary")
        add("")
        add(report["analyst_summary"])
        add("")

    artifacts = _session_artifacts(result.run_dir)
    if artifacts:
        add("## Files the session produced")
        add("")
        for name, size in artifacts:
            add(f"- [`{name}`]({name}) <sub>{size}</sub>")
        add("")

    add("---")
    add("")
    add(
        f"<sub>Simulated participant. Would return: {_fmt(report.get('would_return'))} · "
        f"would recommend: {_fmt(report.get('would_recommend'))} · "
        f"pages visited: {len(report.get('pages_visited') or [])} · "
        f"raw log: `stdout.log`</sub>"
    )
    add("")
    return "\n".join(out)


# --------------------------------------------------------------------------
# study-level markdown
# --------------------------------------------------------------------------


def _aggregate_findings(results: Iterable[RunResult]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for result in results:
        for finding in result.report.get("friction_points") or []:
            rows.append({**finding, "persona": result.spec.persona.name,
                         "task": result.spec.task.title, "run_id": result.spec.run_id})
    order = {s: i for i, s in enumerate(SEVERITIES)}
    rows.sort(key=lambda r: order.get(r["severity"], 99))
    return rows


def render_index_markdown(results: list[RunResult], study_name: str, meta: dict[str, Any]) -> str:
    out: list[str] = []
    add = out.append
    add(f"# UX probe: {study_name}")
    add("")
    add(f"<sub>{meta.get('started_at', '')} · {len(results)} session"
        f"{'s' if len(results) != 1 else ''} · "
        f"agents: {', '.join(sorted({r.spec.agent for r in results}))}</sub>")
    add("")

    totals = {s: 0 for s in SEVERITIES}
    for result in results:
        for sev, n in severity_counts(result.report).items():
            totals[sev] += n
    outcomes: dict[str, int] = {}
    for result in results:
        key = result.report.get("outcome", "unknown")
        outcomes[key] = outcomes.get(key, 0) + 1

    stats = study_stats(results)
    add("## At a glance")
    add("")
    add("| | |")
    add("|---|---|")
    add(f"| Task outcomes | {'  '.join(f'{OUTCOME_EMOJI.get(k, chr(10067))} {v} {k}' for k, v in sorted(outcomes.items()))} |")
    add(f"| Fix first | **{stats['fix_first']}** issue(s) |")
    add(f"| Issues | **{stats['issues']}** distinct, merged from {stats['raw_findings']} raw findings |")
    add(f"| Hit by everyone | {stats['universal']} |")
    add(f"| Evidence quality | {stats['measured']} measured in the page"
        + (f", {stats['impressions']} unevidenced" if stats["impressions"] else "")
        + " |")
    if stats["spend"] or stats["minutes"]:
        cost = f"${stats['spend']:.2f} · " if stats["spend"] else ""
        add(f"| Cost of the study | {cost}{stats['minutes']} minutes of agent time |")
    problems = []
    if stats["failed"]:
        problems.append(f"{stats['failed']} session(s) produced no report")
    if stats["truncated"]:
        problems.append(f"{stats['truncated']} salvaged from a cut-short transcript")
    if problems:
        add(f"| Caveats | {'; '.join(problems)} |")
    add("")

    add("## Sessions")
    add("")
    add("| Persona | Task | Outcome | Difficulty | Ease | Blockers | One thing to fix | Report |")
    add("|---|---|:--:|:--:|:--:|:--:|---|---|")
    for result in results:
        report = result.report
        counts = severity_counts(report)
        rel = os.path.basename(result.run_dir)
        add(
            "| {p} | {t} | {o} {ot} | {d} | {e} | {b} | {fix} | [log]({rel}/report.md) |".format(
                p=_md_escape_cell(result.spec.persona.name),
                t=_md_escape_cell(result.spec.task.title),
                o=OUTCOME_EMOJI.get(report.get("outcome", "unknown"), "❔"),
                ot=report.get("outcome", "unknown"),
                d=_fmt(report.get("difficulty")),
                e=_fmt(report.get("ease_score")),
                b=counts["blocker"] or "-",
                fix=_md_escape_cell(report.get("one_thing_to_fix", "")),
                rel=rel,
            )
        )
    add("")

    groups = prioritise(results)
    if groups:
        for band, heading, blurb in (
            (BAND_FIX_FIRST, "Fix first",
             "Blockers, and anything several participants hit and agreed was bad."),
            (BAND_NEXT, "Next",
             "Real damage, but narrower reach or lighter severity."),
            (BAND_BACKLOG, "Backlog", "Polish and one-off annoyances."),
        ):
            band_groups = [g for g in groups if g["band"] == band]
            if not band_groups:
                continue
            add(f"## {heading} <sub>({len(band_groups)})</sub>")
            add("")
            add(f"<sub>{blurb}</sub>")
            add("")
            for group in band_groups:
                add(f"**{group['rank']}. {SEV_EMOJI.get(group['severity'], '·')} "
                    f"{group['what']}**")
                add("")
                bits = [
                    f"`{group['severity']}`",
                    f"hit by **{group['reach']}/{group['total_personas']}**"
                    + (", everyone" if group["universal"] else ""),
                    f"evidence: **{group['grade']}**",
                    f"impact {group['impact']}",
                ]
                if group.get("where"):
                    bits.insert(1, group["where"])
                if group["disputed"]:
                    bits.append(f"⚖ rated {' / '.join(group['severities'])} by different people")
                if group["named_by"]:
                    bits.append("★ named as *the* thing to fix by "
                                + ", ".join(n.split(",")[0] for n in group["named_by"]))
                add("  " + " · ".join(bits))
                add("")
                if group.get("why_it_hurts"):
                    add(f"  {group['why_it_hurts']}")
                    add("")
                for quote in group.get("evidence", [])[:2]:
                    add(f"  > {quote}")
                    add("")
                if group.get("fixes"):
                    add(f"  **Fix:** {group['fixes'][0]}")
                    add("")
        add("")

    delights = [(r.spec.persona.name, d) for r in results for d in (r.report.get("delights") or [])]
    if delights:
        add("## What worked")
        add("")
        for who, item in delights:
            add(f"- {item} <sub>({who})</sub>")
        add("")

    add("---")
    add("")
    add("<sub>These are simulated participants driven by a coding agent, not real users. "
        "Mechanical observations (a control that does not respond, an unlabelled input, a "
        "console error) are reliable. Statements about how a person *feels* are plausible "
        "hypotheses to test with real people, not measurements.</sub>")
    add("")
    return "\n".join(out)


# --------------------------------------------------------------------------
# HTML
# --------------------------------------------------------------------------
# The dashboard lives in dashboard.py; these names are re-exported below so
# `from uxprobe.reporting import render_index_html` keeps working.


# --------------------------------------------------------------------------
# CSV
# --------------------------------------------------------------------------

_CSV_FIELDS = ["rank", "band", "impact", "severity", "what", "where", "reach",
               "total_personas", "universal", "evidence_grade", "disputed", "personas",
               "why_it_hurts", "suggested_fix", "evidence", "heuristic", "named_by"]


def write_findings_csv(results: list[RunResult], path: str) -> int:
    """One row per *merged issue*, ranked, a triage list, not a dump of raw findings."""
    rows = 0
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=_CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for group in prioritise(results):
            writer.writerow(
                {
                    "rank": group["rank"],
                    "band": group["band"],
                    "impact": group["impact"],
                    "severity": group["severity"],
                    "what": group["what"],
                    "where": group.get("where", ""),
                    "reach": group["reach"],
                    "total_personas": group["total_personas"],
                    "universal": "yes" if group["universal"] else "",
                    "evidence_grade": group["grade"],
                    "disputed": " / ".join(group["severities"]) if group["disputed"] else "",
                    "personas": "; ".join(group["personas"]),
                    "why_it_hurts": group.get("why_it_hurts", ""),
                    "suggested_fix": "; ".join(group.get("fixes", [])[:2]),
                    "evidence": " | ".join(group.get("evidence", [])[:3]),
                    "heuristic": "; ".join(sorted(group.get("heuristics", []))),
                    "named_by": "; ".join(group.get("named_by", [])),
                }
            )
            rows += 1
    return rows


def write_tickets_markdown(results: list[RunResult], path: str, study_name: str) -> int:
    """Paste-into-the-tracker issue blocks, worst first."""
    groups = prioritise(results)
    out = [f"# {study_name}: issues to triage", ""]
    out += [f"<sub>{len(groups)} merged issues. Each block is self-contained; copy the ones "
            "you want into your tracker.</sub>", ""]
    for band, label in ((BAND_FIX_FIRST, "Fix first"), (BAND_NEXT, "Next"),
                        (BAND_BACKLOG, "Backlog")):
        band_groups = [g for g in groups if g["band"] == band]
        if not band_groups:
            continue
        out += [f"## {label}", ""]
        for group in band_groups:
            out.append(issue_ticket(group))
            out.append("---")
            out.append("")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(out))
    return len(groups)


def write_summary_json(results: list[RunResult], path: str, meta: dict[str, Any]) -> None:
    payload = {"meta": meta, "runs": [r.to_dict() for r in results]}
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


from .dashboard import (  # noqa: E402  (re-exported for callers of this module)
    LOGO_MARK,
    persona_icon,
    render_index_html,
    render_session_html,
)

__all__ = [
    "render_run_markdown", "render_index_markdown", "render_index_html",
    "render_session_html", "persona_icon", "LOGO_MARK",
    "write_findings_csv", "write_tickets_markdown", "write_summary_json",
]
