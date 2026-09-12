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

_HTML_HEAD = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>uxprobe · __TITLE__</title>
<script>try{document.documentElement.className="js"}catch(e){}</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Schibsted+Grotesk:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;600&display=swap" rel="stylesheet">
<style>
*{margin:0;box-sizing:border-box}
:root{
  color-scheme:dark;
  --bg:#0a0a0b; --panel:#0f0f11; --panel-2:#141519; --raise:#181a1f;
  --ink:#e8e9ec; --ink-soft:#b7bac1; --muted:#868b95; --faint:#585d67;
  --line:rgba(255,255,255,.06); --line-2:rgba(255,255,255,.11); --line-3:rgba(255,255,255,.16);
  --accent:#6e79ff; --accent-ink:#b3b8ff; --accent-bg:rgba(110,121,255,.13);
  --blocker:#f26470; --major:#e0a44e; --minor:#6f90e6; --nitpick:#7b818c; --ok:#46c98a;
  --mono:"JetBrains Mono",ui-monospace,SFMono-Regular,Menlo,monospace;
}
@media(prefers-color-scheme:light){:root{
  color-scheme:light;
  --bg:#fbfbfc; --panel:#ffffff; --panel-2:#f6f7f9; --raise:#eef0f3;
  --ink:#16181d; --ink-soft:#3c4149; --muted:#6a707b; --faint:#a0a5af;
  --line:rgba(10,12,20,.09); --line-2:rgba(10,12,20,.14); --line-3:rgba(10,12,20,.2);
  --accent:#4b57e6; --accent-ink:#3a45c9; --accent-bg:rgba(75,87,230,.09);
  --blocker:#d63a4a; --major:#b9761b; --minor:#3a5bd0; --nitpick:#6a707b; --ok:#0f9d63;
}}
html,body{height:100%}
body{margin:0;background:var(--bg);color:var(--ink);
  font:14px/1.6 "Schibsted Grotesk",ui-sans-serif,-apple-system,"Segoe UI",Roboto,sans-serif;
  -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
::selection{background:var(--accent);color:#fff}

/* film grain overlay */
/* Static grain: no blend mode (keeps repaints cheap so scrolling and the
   sidebar toggle stay smooth). */
.grain{position:fixed;inset:0;z-index:80;pointer-events:none;opacity:.028;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='140' height='140'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")}
@media(prefers-color-scheme:light){.grain{opacity:.04}}
.ic{width:16px;height:16px;flex:none;display:inline-block;vertical-align:middle}
a{color:var(--accent-ink);text-decoration:none}
a:hover{text-decoration:underline}

/* app shell */
.app{display:grid;grid-template-columns:248px minmax(0,1fr);min-height:100vh}
.side{position:sticky;top:0;height:100vh;border-right:1px solid var(--line);overflow:hidden;
  background:var(--panel);display:flex;flex-direction:column;padding:18px 14px;gap:6px}
.side-top{display:flex;align-items:center;gap:8px;padding:2px 6px 14px}
.brand{display:flex;align-items:center;gap:10px;min-width:0}
.brand .mark{width:28px;height:28px;border-radius:8px;flex:none;display:grid;place-items:center;
  background:var(--accent);box-shadow:0 4px 14px -4px var(--accent)}
.brand .mark .logo{width:17px;height:17px;display:block}
.brand .word{font-weight:650;letter-spacing:-.01em;font-size:.95rem;white-space:nowrap}
.brand .word span{color:var(--muted);font-weight:450}
.side-toggle{margin-left:auto;flex:none;width:30px;height:30px;display:grid;place-items:center;
  border:1px solid var(--line-2);border-radius:8px;background:transparent;color:var(--muted);cursor:pointer;
  transition:color .12s,border-color .12s,background .12s}
.side-toggle:hover{color:var(--ink);border-color:var(--line-3);background:var(--panel-2)}
.side-toggle .ic{width:17px;height:17px}
/* collapsed rail */
.app.collapsed{grid-template-columns:68px minmax(0,1fr)}
.app.collapsed .side{padding:18px 10px;align-items:stretch}
.app.collapsed .side-top{flex-direction:column;gap:12px;padding:2px 0 14px;align-items:center}
.app.collapsed .brand .word,.app.collapsed .navlabel,
.app.collapsed .nav a span,.app.collapsed .side .foot{display:none}
.app.collapsed .side-toggle{margin:0}
.app.collapsed .nav a{justify-content:center;padding:10px 0}
.navlabel{color:var(--faint);font-size:.66rem;font-weight:600;text-transform:uppercase;
  letter-spacing:.12em;padding:10px 10px 4px}
.nav{display:flex;flex-direction:column;gap:2px}
.nav a{display:flex;align-items:center;gap:10px;padding:7px 10px;border-radius:8px;
  color:var(--ink-soft);font-weight:500;font-size:.87rem;cursor:pointer;
  border:1px solid transparent;transition:background .12s,color .12s}
.nav a .ic{width:17px;height:17px;flex:none;color:var(--faint)}
.nav a .n{margin-left:auto;font-variant-numeric:tabular-nums;color:var(--faint);
  font-size:.75rem;font-weight:600}
.nav a:hover{background:var(--panel-2);color:var(--ink)}
.js .nav a.active{background:var(--accent-bg);color:var(--accent-ink);border-color:var(--line-2)}
.js .nav a.active .ic,.js .nav a.active .n{color:var(--accent-ink)}
.side .foot{margin-top:auto;border-top:1px solid var(--line);padding:12px 10px 4px;
  color:var(--muted);font-size:.76rem;line-height:1.5}
.side .foot .row{display:flex;justify-content:space-between;gap:8px}
.side .foot .row span:last-child{color:var(--ink-soft);font-weight:500;
  font-variant-numeric:tabular-nums;text-align:right}
.side .foot .name{color:var(--ink);font-weight:600;font-size:.82rem;margin-bottom:8px;
  word-break:break-word}

/* main */
.main{min-width:0;display:flex;flex-direction:column}
.topbar{position:sticky;top:0;z-index:5;display:flex;align-items:center;gap:12px;
  padding:0 34px;height:56px;border-bottom:1px solid var(--line);background:var(--bg)}
.crumb{display:flex;align-items:center;gap:8px;color:var(--muted);font-size:.82rem}
.crumb b{color:var(--ink);font-weight:600}
.crumb .sep{color:var(--faint)}
.pillbtns{margin-left:auto;display:flex;gap:4px}
.content{padding:26px 34px 64px;width:100%}
.view{display:block}
.js .view{display:none}
.js .view.active{display:block;animation:fade .18s ease}
@keyframes fade{from{opacity:0;transform:translateY(3px)}to{opacity:1;transform:none}}
.vhead{margin:2px 0 18px}
.vhead h1{font-size:1.35rem;font-weight:650;letter-spacing:-.02em}
.vhead p{color:var(--muted);font-size:.86rem;margin-top:4px;max-width:62ch}

/* KPI strip */
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--line);
  border:1px solid var(--line);border-radius:12px;overflow:hidden;margin-bottom:20px}
.kpi{background:var(--panel);padding:16px 18px}
.kpi .k{color:var(--muted);font-size:.72rem;font-weight:600;text-transform:uppercase;letter-spacing:.06em}
.kpi .v{font-family:var(--mono);font-size:1.9rem;font-weight:600;letter-spacing:-.02em;
  margin-top:8px;line-height:1;font-variant-numeric:tabular-nums}
.kpi .v small{color:var(--faint);font-size:.9rem}
.kpi .v.blocker{color:var(--blocker)} .kpi .v.ok{color:var(--ok)} .kpi .v.accent{color:var(--accent-ink)}
.kpi .note{color:var(--muted);font-size:.75rem;margin-top:6px}

.panel{background:var(--panel);border:1px solid var(--line);border-radius:12px}
.panel + .panel{margin-top:16px}
.panel .ph{padding:13px 18px;border-bottom:1px solid var(--line);display:flex;align-items:center;gap:10px}
.panel .ph h3{font-size:.82rem;font-weight:600;letter-spacing:.01em}
.panel .ph .sub{color:var(--muted);font-size:.76rem}
.panel .pb{padding:16px 18px}

/* signal / distribution bars */
.dist{display:flex;height:10px;border-radius:6px;overflow:hidden;background:var(--raise);gap:2px}
.dist i{display:block;height:100%}
.sev-blocker{background:var(--blocker)} .sev-major{background:var(--major)}
.sev-minor{background:var(--minor)} .sev-nitpick{background:var(--nitpick)}
.seg-completed{background:var(--ok)} .seg-partial{background:var(--major)}
.seg-abandoned{background:var(--blocker)} .seg-failed{background:var(--faint)} .seg-unknown{background:var(--faint)}
.lg{display:flex;flex-wrap:wrap;gap:16px;margin-top:12px;font-size:.78rem;color:var(--muted)}
.lg span{display:inline-flex;align-items:center;gap:7px}
.lg i{width:9px;height:9px;border-radius:3px;flex:none}
.lg b{color:var(--ink);font-weight:600;font-variant-numeric:tabular-nums}

/* table */
.scroll{overflow-x:auto;-webkit-overflow-scrolling:touch}
table{width:100%;border-collapse:collapse;font-size:.86rem}
thead th{position:sticky;top:56px;background:var(--panel);z-index:1}
th,td{text-align:left;padding:12px 14px;border-bottom:1px solid var(--line);vertical-align:middle}
tbody tr:last-child td{border-bottom:0}
tbody tr:hover{background:var(--panel-2)}
th{color:var(--faint);font-weight:600;font-size:.68rem;text-transform:uppercase;letter-spacing:.07em}
td.num{font-family:var(--mono);font-variant-numeric:tabular-nums;color:var(--ink-soft)}
.who{display:flex;align-items:center;gap:10px;min-width:170px}
.ava{width:30px;height:30px;border-radius:8px;flex:none;display:grid;place-items:center;
  color:#fff;background:var(--accent)}
.ava .ic{width:60%;height:60%}
.who .nm{font-weight:550} .who .dev{color:var(--muted);font-size:.74rem;text-transform:capitalize}
.fixcell{max-width:34rem;color:var(--ink-soft);font-size:.84rem}
.badge{display:inline-flex;align-items:center;gap:6px;font-size:.76rem;font-weight:550;
  padding:3px 9px;border-radius:6px;border:1px solid var(--line-2);white-space:nowrap;text-transform:capitalize}
.badge .st{width:6px;height:6px;border-radius:99px;background:var(--muted)}
.badge.completed{color:var(--ok)} .badge.completed .st{background:var(--ok)}
.badge.partial{color:var(--major)} .badge.partial .st{background:var(--major)}
.badge.abandoned,.badge.failed{color:var(--blocker)}
.badge.abandoned .st,.badge.failed .st{background:var(--blocker)}
.meter{display:flex;align-items:center;gap:8px;font-family:var(--mono);font-size:.8rem}
.meter .track{width:46px;height:5px;border-radius:99px;background:var(--raise);overflow:hidden;flex:none}
.meter .fill{height:100%;border-radius:99px;background:var(--accent)}
.bnum{font-family:var(--mono);font-weight:600;color:var(--blocker)}
.zero{color:var(--faint)}
.linklog{color:var(--muted);font-size:.76rem;font-weight:550;border:1px solid var(--line-2);
  border-radius:7px;padding:4px 10px;white-space:nowrap}
.linklog:hover{color:var(--ink);border-color:var(--line-3);text-decoration:none;background:var(--panel-2)}

/* issues */
.band{display:flex;align-items:center;gap:8px;margin:22px 0 10px;font-size:.72rem;font-weight:600;
  text-transform:uppercase;letter-spacing:.1em;color:var(--muted)}
.band:first-child{margin-top:4px}
.band .count{background:var(--raise);border:1px solid var(--line-2);color:var(--ink);
  border-radius:99px;padding:1px 8px;font-size:.7rem}
.f{position:relative;background:var(--panel);border:1px solid var(--line);
  border-radius:11px;padding:15px 17px;margin:9px 0;transition:border-color .12s,background .12s}
.f:hover{border-color:var(--line-2);background:var(--panel-2)}
.f.blocker{--edge:var(--blocker)} .f.major{--edge:var(--major)}
.f.minor{--edge:var(--minor)} .f.nitpick{--edge:var(--nitpick)}
.f .head{display:flex;gap:12px;align-items:baseline}
.f .rank{font-family:var(--mono);font-size:.82rem;font-weight:600;color:var(--faint);flex:none;min-width:2.2ch}
.f .what{color:var(--ink);font-weight:550;font-size:.95rem;line-height:1.45;flex:1}
.pill{display:inline-block;padding:1px 7px;border-radius:5px;font-size:.63rem;font-weight:700;
  text-transform:uppercase;letter-spacing:.05em;margin-right:8px;vertical-align:middle;
  color:var(--edge,var(--muted));border:1px solid currentColor}
.tags{display:flex;flex-wrap:wrap;gap:6px;margin:10px 0 0;padding-left:calc(2.2ch + 12px)}
.tag{font-size:.72rem;font-weight:550;padding:2px 8px;border-radius:6px;background:var(--raise);
  border:1px solid var(--line);color:var(--ink-soft);white-space:nowrap}
.tag.hot{background:transparent;border-color:var(--blocker);color:var(--blocker)}
.tag.star{background:transparent;border-color:var(--major);color:var(--major)}
.tag.grade-measured{border-color:color-mix(in srgb,var(--ok) 50%,transparent);color:var(--ok)}
.tag.grade-impression{border-style:dashed;color:var(--muted)}
.f .meta{color:var(--muted);font-size:.78rem;margin-top:10px;padding-left:calc(2.2ch + 12px)}
.f .fix{color:var(--ink-soft);font-size:.85rem;margin-top:9px;padding-left:calc(2.2ch + 12px)}
.f .fix strong{color:var(--ink);font-weight:600}
details{margin:8px 0 0;padding-left:calc(2.2ch + 12px)}
summary{cursor:pointer;color:var(--muted);font-size:.78rem;font-weight:550;list-style:none;
  display:inline-flex;align-items:center;gap:6px}
summary::-webkit-details-marker{display:none}
summary::before{content:"+";color:var(--accent-ink);font-family:var(--mono);font-weight:700}
details[open] summary::before{content:"\2212"}
details ul{margin:8px 0 0;padding-left:16px;color:var(--ink-soft);font-size:.82rem}
details li{margin:3px 0}

/* gallery */
.gal + .gal{margin-top:22px}
.gal h4{font-size:.85rem;font-weight:600;margin-bottom:10px;display:flex;align-items:center;gap:9px}
.gal h4 .ava{width:24px;height:24px;border-radius:6px;font-size:.7rem}
.strip{display:flex;gap:12px;overflow-x:auto;padding-bottom:8px;scroll-snap-type:x proximity}
.strip figure{margin:0;flex:0 0 232px;scroll-snap-align:start}
.strip a{display:block}
.strip img{width:100%;height:150px;object-fit:cover;object-position:top left;border-radius:9px;
  border:1px solid var(--line);background:var(--panel-2);display:block}
.strip a:hover img{border-color:var(--line-3)}
.strip figcaption{color:var(--muted);font-size:.75rem;margin-top:8px;line-height:1.4}

/* voices */
.quote{background:var(--panel);border:1px solid var(--line);border-radius:10px;
  padding:16px 18px;margin:10px 0}
.quote p{color:var(--ink-soft);font-size:.95rem;line-height:1.6}
.quote .cite{display:flex;align-items:center;gap:9px;margin-top:12px;color:var(--muted);font-size:.8rem;font-weight:550}
.quote .cite .ava{width:24px;height:24px;border-radius:6px;font-size:.7rem}
.worked{list-style:none;padding:0;margin:0;display:grid;gap:8px;grid-template-columns:repeat(auto-fill,minmax(300px,1fr))}
.worked li{background:var(--panel);border:1px solid var(--line);border-radius:9px;
  padding:11px 13px 11px 34px;position:relative;font-size:.86rem;color:var(--ink-soft)}
.worked li::before{content:"\2713";position:absolute;left:13px;top:11px;color:var(--ok);font-weight:700}
.worked .by{color:var(--muted);font-size:.78rem}

.empty{color:var(--muted);font-size:.88rem;padding:26px;text-align:center;
  border:1px dashed var(--line-2);border-radius:12px}
.foot{color:var(--faint);font-size:.78rem;margin-top:26px;padding-top:16px;border-top:1px solid var(--line);line-height:1.65;max-width:70ch}

/* log modal */
.modal{position:fixed;inset:0;z-index:120;display:none;justify-content:center;
  align-items:flex-start;padding:44px 20px;overflow-y:auto;
  background:rgba(6,7,10,.62);backdrop-filter:blur(3px)}
.modal.open{display:flex}
.modal-card{background:var(--panel);border:1px solid var(--line-2);border-radius:14px;
  width:min(880px,100%);box-shadow:0 40px 100px -30px rgba(0,0,0,.7);margin:auto}
.modal-head{position:sticky;top:0;z-index:1;display:flex;align-items:center;gap:12px;
  padding:14px 20px;border-bottom:1px solid var(--line);background:var(--panel);border-radius:14px 14px 0 0}
.modal-head .t{font-weight:600;font-size:.92rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.modal-close{margin-left:auto;flex:none;width:32px;height:32px;display:grid;place-items:center;
  border:1px solid var(--line-2);border-radius:8px;background:var(--raise);color:var(--muted);cursor:pointer}
.modal-close:hover{color:var(--ink);border-color:var(--line-3)}
.modal-close .ic{width:16px;height:16px}
.modal-body{padding:22px 26px 30px}

/* rendered session document */
.logdoc h2{font-size:1.15rem;font-weight:700;letter-spacing:-.01em;line-height:1.3;margin-bottom:6px}
.logdoc h2 .arrow{color:var(--faint);font-weight:400}
.logdoc h3{font-size:.82rem;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);
  font-weight:600;margin:24px 0 10px;padding-bottom:8px;border-bottom:1px solid var(--line)}
.logdoc p{color:var(--ink-soft);margin:8px 0}
.logdoc p.one{font-size:1rem;color:var(--ink)}
.chips-row{display:flex;flex-wrap:wrap;gap:6px;margin:12px 0 4px}
.chip{font-size:.74rem;font-weight:500;color:var(--ink-soft);background:var(--raise);
  border:1px solid var(--line);border-radius:6px;padding:3px 9px;text-transform:capitalize}
.logdoc .warn{margin:12px 0;padding:10px 12px;border-radius:8px;color:var(--blocker);
  border:1px solid color-mix(in srgb,var(--blocker) 40%,transparent);background:color-mix(in srgb,var(--blocker) 8%,transparent)}
.logdoc ul.kv{list-style:none;padding:0;margin:4px 0;display:grid;gap:6px}
.logdoc ul.kv li{color:var(--ink-soft);font-size:.88rem}
.logdoc ul.kv b{display:inline-block;min-width:64px;color:var(--muted);font-weight:600;margin-right:6px}
.logdoc ul{padding-left:20px} .logdoc li{margin:4px 0;color:var(--ink-soft)}
.logdoc blockquote{margin:8px 0;padding:10px 14px;border-left:3px solid var(--line-2);
  background:var(--panel-2);border-radius:0 8px 8px 0;color:var(--ink-soft);font-style:italic}
.logdoc table{width:100%;border-collapse:collapse;font-size:.8rem;margin:8px 0}
.logdoc th,.logdoc td{border:1px solid var(--line);padding:7px 9px;text-align:left;vertical-align:top}
.logdoc th{background:var(--panel-2);color:var(--muted);font-weight:600;font-size:.68rem;
  text-transform:uppercase;letter-spacing:.05em}
.logdoc td.num{font-family:var(--mono);color:var(--ink-soft)}
.logdoc details{margin:10px 0}
.logdoc summary{cursor:pointer;color:var(--accent-ink);font-weight:550;font-size:.84rem}
.logdoc .think{margin-top:10px}
.logdoc .think img{display:block;width:100%;max-width:520px;border:1px solid var(--line);
  border-radius:8px;margin:8px 0}
.logdoc .lf{border:1px solid var(--line);border-radius:9px;padding:11px 13px;margin:8px 0;background:var(--panel-2)}
.logdoc .lf .pill{color:var(--edge,var(--muted))}
.logdoc .lf.blocker{--edge:var(--blocker)} .logdoc .lf.major{--edge:var(--major)}
.logdoc .lf.minor{--edge:var(--minor)} .logdoc .lf.nitpick{--edge:var(--nitpick)}
.logdoc .lf b{color:var(--ink)}
.logdoc .lfrow{margin-top:6px;font-size:.84rem;color:var(--ink-soft)}
.logdoc .lfrow b{color:var(--muted);font-weight:600;margin-right:6px}

@media(max-width:840px){
  .app{grid-template-columns:1fr}
  .side{position:static;height:auto;flex-direction:row;flex-wrap:wrap;align-items:center;
    border-right:0;border-bottom:1px solid var(--line)}
  .side .foot{display:none}
  .navlabel{display:none}
  .nav{flex-direction:row;flex-wrap:wrap}
  .nav a .n{margin-left:6px}
  .kpis{grid-template-columns:repeat(2,1fr)}
  thead th{top:0}
}
</style></head><body>
"""


def _pill(sev: str) -> str:
    return f'<span class="pill {sev}">{sev}</span>'


# Progressive enhancement only: with JS disabled every view is shown stacked and
# the page reads top to bottom. With JS, the sidebar switches between views.
_HTML_TAIL_JS = """<script>
(function(){
  if(document.documentElement.className.indexOf("js")<0){return;}
  var navs=[].slice.call(document.querySelectorAll(".nav a[data-view]"));
  var views=[].slice.call(document.querySelectorAll(".view"));
  function countUp(el){
    var target=parseFloat(el.getAttribute("data-count"));
    if(isNaN(target)){return;}
    var t0=null,dur=750;
    function step(ts){if(!t0){t0=ts;}var p=Math.min(1,(ts-t0)/dur);
      el.textContent=Math.round(target*(1-Math.pow(1-p,3))).toString();
      if(p<1){requestAnimationFrame(step);}}
    requestAnimationFrame(step);
  }
  function show(id){
    views.forEach(function(v){v.classList.toggle("active",v.id===id);});
    navs.forEach(function(a){a.classList.toggle("active",a.getAttribute("data-view")===id);});
    var v=document.getElementById(id);
    if(v){[].slice.call(v.querySelectorAll("[data-count]")).forEach(countUp);}
    window.scrollTo(0,0);
  }
  navs.forEach(function(a){a.addEventListener("click",function(e){
    e.preventDefault();var id=a.getAttribute("data-view");
    if(history.replaceState){history.replaceState(null,"","#"+id);}
    show(id);
  });});
  var ids=views.map(function(v){return v.id;});
  var initial=(location.hash||"").replace("#","");
  show(ids.indexOf(initial)>=0?initial:(ids[0]||""));
  window.addEventListener("hashchange",function(){
    var h=(location.hash||"").replace("#","");if(ids.indexOf(h)>=0){show(h);}
  });

  // collapsible sidebar (remembered per browser)
  var app=document.querySelector(".app");
  var toggle=document.querySelector(".side-toggle");
  if(app&&toggle){
    try{if(localStorage.getItem("uxprobe-side")==="collapsed"){app.classList.add("collapsed");}}catch(e){}
    toggle.addEventListener("click",function(){
      var c=app.classList.toggle("collapsed");
      toggle.setAttribute("title",c?"Expand sidebar":"Collapse sidebar");
      try{localStorage.setItem("uxprobe-side",c?"collapsed":"open");}catch(e){}
    });
  }

  // log modal
  var modal=document.getElementById("logmodal");
  if(modal){
    var body=modal.querySelector(".modal-body");
    var title=modal.querySelector(".modal-head .t");
    function openLog(id){
      var src=document.getElementById(id);
      if(!src){return;}
      body.innerHTML=src.innerHTML;
      title.textContent=src.getAttribute("data-title")||"Session log";
      modal.classList.add("open");modal.setAttribute("aria-hidden","false");
      document.body.style.overflow="hidden";body.scrollTop=0;
    }
    function closeLog(){
      modal.classList.remove("open");modal.setAttribute("aria-hidden","true");
      document.body.style.overflow="";body.innerHTML="";
    }
    document.querySelectorAll("[data-log]").forEach(function(btn){
      btn.addEventListener("click",function(){openLog(btn.getAttribute("data-log"));});
    });
    modal.addEventListener("click",function(e){if(e.target===modal){closeLog();}});
    modal.querySelector(".modal-close").addEventListener("click",closeLog);
    document.addEventListener("keydown",function(e){if(e.key==="Escape"){closeLog();}});
  }
})();
</script>"""


# Icons are Phosphor (https://phosphoricons.com), inlined so the report stays
# self-contained and works offline. viewBox 0 0 256 256, filled with currentColor.
def _icon(path: str) -> str:
    return (f'<svg class="ic" viewBox="0 0 256 256" fill="currentColor" aria-hidden="true">'
            f'{path}</svg>')


ICON_GRID = _icon('<path d="M104,40H56A16,16,0,0,0,40,56v48a16,16,0,0,0,16,16h48a16,16,0,0,0,16-16V56A16,16,0,0,0,104,40Zm0,64H56V56h48v48Zm96-64H152a16,16,0,0,0-16,16v48a16,16,0,0,0,16,16h48a16,16,0,0,0,16-16V56A16,16,0,0,0,200,40Zm0,64H152V56h48v48Zm-96,32H56a16,16,0,0,0-16,16v48a16,16,0,0,0,16,16h48a16,16,0,0,0,16-16V152A16,16,0,0,0,104,136Zm0,64H56V152h48v48Zm96-64H152a16,16,0,0,0-16,16v48a16,16,0,0,0,16,16h48a16,16,0,0,0,16-16V152A16,16,0,0,0,200,136Zm0,64H152V152h48v48Z"/>')
ICON_ROWS = _icon('<path d="M80,64a8,8,0,0,1,8-8H216a8,8,0,0,1,0,16H88A8,8,0,0,1,80,64Zm136,56H88a8,8,0,0,0,0,16H216a8,8,0,0,0,0-16Zm0,64H88a8,8,0,0,0,0,16H216a8,8,0,0,0,0-16ZM44,52A12,12,0,1,0,56,64,12,12,0,0,0,44,52Zm0,64a12,12,0,1,0,12,12A12,12,0,0,0,44,116Zm0,64a12,12,0,1,0,12,12A12,12,0,0,0,44,180Z"/>')
ICON_FLAG = _icon('<path d="M242.63,96.44l-184-64A8,8,0,0,0,48,40V216a8,8,0,0,0,16,0V173.69l178.63-62.13a8,8,0,0,0,0-15.12ZM64,156.75V51.25L215.65,104Z"/>')
ICON_IMAGE = _icon('<path d="M208,32H48A16,16,0,0,0,32,48V208a16,16,0,0,0,16,16H208a16,16,0,0,0,16-16V48A16,16,0,0,0,208,32ZM48,48H208v77.38l-24.69-24.7a16,16,0,0,0-22.62,0L53.37,208H48ZM208,208H76l96-96,36,36v60ZM96,120A24,24,0,1,0,72,96,24,24,0,0,0,96,120Zm0-32a8,8,0,1,1-8,8A8,8,0,0,1,96,88Z"/>')
ICON_QUOTE = _icon('<path d="M100,56H40A16,16,0,0,0,24,72v64a16,16,0,0,0,16,16h60v8a32,32,0,0,1-32,32,8,8,0,0,0,0,16,48.05,48.05,0,0,0,48-48V72A16,16,0,0,0,100,56Zm0,80H40V72h60ZM216,56H156a16,16,0,0,0-16,16v64a16,16,0,0,0,16,16h60v8a32,32,0,0,1-32,32,8,8,0,0,0,0,16,48.05,48.05,0,0,0,48-48V72A16,16,0,0,0,216,56Zm0,80H156V72h60Z"/>')
ICON_X = _icon('<path d="M205.66,194.34a8,8,0,0,1-11.32,11.32L128,139.31,61.66,205.66a8,8,0,0,1-11.32-11.32L116.69,128,50.34,61.66A8,8,0,0,1,61.66,50.34L128,116.69l66.34-66.35a8,8,0,0,1,11.32,11.32L139.31,128Z"/>')
ICON_SIDEBAR = _icon('<path d="M216,40H40A16,16,0,0,0,24,56V200a16,16,0,0,0,16,16H216a16,16,0,0,0,16-16V56A16,16,0,0,0,216,40ZM40,56H80V200H40ZM216,200H96V56H216V200Z"/>')

# A bespoke wordmark: a probe crosshair, drawn white on the accent tile.
LOGO_MARK = ('<svg class="logo" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" '
             'stroke-linecap="round"><circle cx="12" cy="12" r="6.4"/>'
             '<path d="M12 1.7v3.2M12 19.1v3.2M1.7 12h3.2M19.1 12h3.2"/>'
             '<circle cx="12" cy="12" r="1.7" fill="#fff" stroke="none"/></svg>')

# One Phosphor glyph per persona, so each participant reads at a glance.
_PERSONA_GLYPHS = {
    "first-timer": _icon('<path d="M197.58,129.06,146,110l-19-51.62a15.92,15.92,0,0,0-29.88,0L78,110l-51.62,19a15.92,15.92,0,0,0,0,29.88L78,178l19,51.62a15.92,15.92,0,0,0,29.88,0L146,178l51.62-19a15.92,15.92,0,0,0,0-29.88ZM137,164.22a8,8,0,0,0-4.74,4.74L112,223.85,91.78,169A8,8,0,0,0,87,164.22L32.15,144,87,123.78A8,8,0,0,0,91.78,119L112,64.15,132.22,119a8,8,0,0,0,4.74,4.74L191.85,144ZM144,40a8,8,0,0,1,8-8h16V16a8,8,0,0,1,16,0V32h16a8,8,0,0,1,0,16H184V64a8,8,0,0,1-16,0V48H152A8,8,0,0,1,144,40ZM248,88a8,8,0,0,1-8,8h-8v8a8,8,0,0,1-16,0V96h-8a8,8,0,0,1,0-16h8V72a8,8,0,0,1,16,0v8h8A8,8,0,0,1,248,88Z"/>'),
    "power-user": _icon('<path d="M215.79,118.17a8,8,0,0,0-5-5.66L153.18,90.9l14.66-73.33a8,8,0,0,0-13.69-7l-112,120a8,8,0,0,0,3,13l57.63,21.61L88.16,238.43a8,8,0,0,0,13.69,7l112-120A8,8,0,0,0,215.79,118.17ZM109.37,214l10.47-52.38a8,8,0,0,0-5-9.06L62,132.71l84.62-90.66L136.16,94.43a8,8,0,0,0,5,9.06l52.8,19.8Z"/>'),
    "mobile-commuter": _icon('<path d="M176,16H80A24,24,0,0,0,56,40V216a24,24,0,0,0,24,24h96a24,24,0,0,0,24-24V40A24,24,0,0,0,176,16ZM72,64H184V192H72Zm8-32h96a8,8,0,0,1,8,8v8H72V40A8,8,0,0,1,80,32Zm96,192H80a8,8,0,0,1-8-8v-8H184v8A8,8,0,0,1,176,224Z"/>'),
    "screen-reader": _icon('<path d="M216,104a8,8,0,0,1-16,0,72,72,0,0,0-144,0c0,26.7,8.53,34.92,17.57,43.64C82.21,156,92,165.41,92,188a36,36,0,0,0,36,36c10.24,0,18.45-4.16,25.83-13.09a8,8,0,1,1,12.34,10.18C155.81,233.64,143,240,128,240a52.06,52.06,0,0,1-52-52c0-15.79-5.68-21.27-13.54-28.84C52.46,149.5,40,137.5,40,104a88,88,0,0,1,176,0Zm-38.13,57.08A8,8,0,0,0,166.93,164,8,8,0,0,1,152,160c0-9.33,4.82-15.76,10.4-23.2,6.37-8.5,13.6-18.13,13.6-32.8a48,48,0,0,0-96,0,8,8,0,0,0,16,0,32,32,0,0,1,64,0c0,9.33-4.82,15.76-10.4,23.2-6.37,8.5-13.6,18.13-13.6,32.8a24,24,0,0,0,44.78,12A8,8,0,0,0,177.87,161.08Z"/>'),
    "skeptical-buyer": _icon('<path d="M239.43,133l-32-80h0a8,8,0,0,0-9.16-4.84L136,62V40a8,8,0,0,0-16,0V65.58L54.26,80.19A8,8,0,0,0,48.57,85h0v.06L16.57,165a7.92,7.92,0,0,0-.57,3c0,23.31,24.54,32,40,32s40-8.69,40-32a7.92,7.92,0,0,0-.57-3L66.92,93.77,120,82V208H104a8,8,0,0,0,0,16h48a8,8,0,0,0,0-16H136V78.42L187,67.1,160.57,133a7.92,7.92,0,0,0-.57,3c0,23.31,24.54,32,40,32s40-8.69,40-32A7.92,7.92,0,0,0,239.43,133ZM56,184c-7.53,0-22.76-3.61-23.93-14.64L56,109.54l23.93,59.82C78.76,180.39,63.53,184,56,184Zm144-32c-7.53,0-22.76-3.61-23.93-14.64L200,77.54l23.93,59.82C222.76,148.39,207.53,152,200,152Z"/>'),
    "impatient-returner": _icon('<path d="M232,136.66A104.12,104.12,0,1,1,119.34,24,8,8,0,0,1,120.66,40,88.12,88.12,0,1,0,216,135.34,8,8,0,0,1,232,136.66ZM120,72v56a8,8,0,0,0,8,8h56a8,8,0,0,0,0-16H136V72a8,8,0,0,0-16,0Zm40-24a12,12,0,1,0-12-12A12,12,0,0,0,160,48Zm36,24a12,12,0,1,0-12-12A12,12,0,0,0,196,72Zm24,36a12,12,0,1,0-12-12A12,12,0,0,0,220,108Z"/>'),
    "cautious-senior": _icon('<path d="M208,40H48A16,16,0,0,0,32,56v56c0,52.72,25.52,84.67,46.93,102.19,23.06,18.86,46,25.26,47,25.53a8,8,0,0,0,4.2,0c1-.27,23.91-6.67,47-25.53C198.48,196.67,224,164.72,224,112V56A16,16,0,0,0,208,40Zm0,72c0,37.07-13.66,67.16-40.6,89.42A129.3,129.3,0,0,1,128,223.62a128.25,128.25,0,0,1-38.92-21.81C61.82,179.51,48,149.3,48,112l0-56,160,0ZM82.34,141.66a8,8,0,0,1,11.32-11.32L112,148.69l50.34-50.35a8,8,0,0,1,11.32,11.32l-56,56a8,8,0,0,1-11.32,0Z"/>'),
    "distracted-multitasker": _icon('<path d="M237.66,178.34a8,8,0,0,1,0,11.32l-24,24a8,8,0,0,1-11.32-11.32L212.69,192H200.94a72.12,72.12,0,0,1-58.59-30.15l-41.72-58.4A56.1,56.1,0,0,0,55.06,80H32a8,8,0,0,1,0-16H55.06a72.12,72.12,0,0,1,58.59,30.15l41.72,58.4A56.1,56.1,0,0,0,200.94,176h11.75l-10.35-10.34a8,8,0,0,1,11.32-11.32ZM143,107a8,8,0,0,0,11.16-1.86l1.2-1.67A56.1,56.1,0,0,1,200.94,80h11.75L202.34,90.34a8,8,0,0,0,11.32,11.32l24-24a8,8,0,0,0,0-11.32l-24-24a8,8,0,0,0-11.32,11.32L212.69,64H200.94a72.12,72.12,0,0,0-58.59,30.15l-1.2,1.67A8,8,0,0,0,143,107Zm-30,42a8,8,0,0,0-11.16,1.86l-1.2,1.67A56.1,56.1,0,0,1,55.06,176H32a8,8,0,0,0,0,16H55.06a72.12,72.12,0,0,0,58.59-30.15l1.2-1.67A8,8,0,0,0,113,149Z"/>'),
    "edge-case-hunter": _icon('<path d="M144,92a12,12,0,1,1,12,12A12,12,0,0,1,144,92ZM100,80a12,12,0,1,0,12,12A12,12,0,0,0,100,80Zm116,64A87.76,87.76,0,0,1,213,167l22.24,9.72A8,8,0,0,1,232,192a7.89,7.89,0,0,1-3.2-.67L207.38,182a88,88,0,0,1-158.76,0L27.2,191.33A7.89,7.89,0,0,1,24,192a8,8,0,0,1-3.2-15.33L43,167A87.76,87.76,0,0,1,40,144v-8H16a8,8,0,0,1,0-16H40v-8a87.76,87.76,0,0,1,3-23L20.8,79.33a8,8,0,1,1,6.4-14.66L48.62,74a88,88,0,0,1,158.76,0l21.42-9.36a8,8,0,0,1,6.4,14.66L213,89.05a87.76,87.76,0,0,1,3,23v8h24a8,8,0,0,1,0,16H216ZM56,120H200v-8a72,72,0,0,0-144,0Zm64,95.54V136H56v8A72.08,72.08,0,0,0,120,215.54ZM200,144v-8H136v79.54A72.08,72.08,0,0,0,200,144Z"/>'),
    "non-native-speaker": _icon('<path d="M247.15,212.42l-56-112a8,8,0,0,0-14.31,0l-21.71,43.43A88,88,0,0,1,108,126.93,103.65,103.65,0,0,0,135.69,64H160a8,8,0,0,0,0-16H104V32a8,8,0,0,0-16,0V48H32a8,8,0,0,0,0,16h87.63A87.76,87.76,0,0,1,96,116.35a87.74,87.74,0,0,1-19-31,8,8,0,1,0-15.08,5.34A103.63,103.63,0,0,0,84,127a87.55,87.55,0,0,1-52,17,8,8,0,0,0,0,16,103.46,103.46,0,0,0,64-22.08,104.18,104.18,0,0,0,51.44,21.31l-26.6,53.19a8,8,0,0,0,14.31,7.16L148.94,192h70.11l13.79,27.58A8,8,0,0,0,240,224a8,8,0,0,0,7.15-11.58ZM156.94,176,184,121.89,211.05,176Z"/>'),
    "_default": _icon('<path d="M230.92,212c-15.23-26.33-38.7-45.21-66.09-54.16a72,72,0,1,0-73.66,0C63.78,166.78,40.31,185.66,25.08,212a8,8,0,1,0,13.85,8c18.84-32.56,52.14-52,89.07-52s70.23,19.44,89.07,52a8,8,0,1,0,13.85-8ZM72,96a56,56,0,1,1,56,56A56.06,56.06,0,0,1,72,96Z"/>'),
}


def persona_icon(persona) -> str:
    return _PERSONA_GLYPHS.get(persona.id, _PERSONA_GLYPHS["_default"])


def render_session_html(result: RunResult, esc=html.escape) -> str:
    """A formatted HTML version of a session report, for the in-page log modal."""
    spec = result.spec
    report = result.report or {}
    persona, task = spec.persona, spec.task
    outcome = report.get("outcome", "unknown")
    rel = os.path.basename(result.run_dir)
    out: list[str] = []
    a = out.append

    a(f'<h2>{esc(persona.name)} <span class="arrow">&rarr;</span> {esc(task.title)}</h2>')
    chips = [f'<span class="badge {esc(outcome)}"><span class="st"></span>{esc(outcome)}</span>',
             f'<span class="chip">difficulty {esc(_fmt(report.get("difficulty")))}/5</span>',
             f'<span class="chip">ease {esc(_fmt(report.get("ease_score")))}/100</span>',
             f'<span class="chip">{esc(spec.agent)}</span>',
             f'<span class="chip">{result.duration_s / 60:.0f}m {result.duration_s % 60:.0f}s</span>']
    turns = result.agent_meta.get("num_turns")
    cost = result.agent_meta.get("total_cost_usd")
    if turns:
        chips.append(f'<span class="chip">{turns} turns</span>')
    if isinstance(cost, (int, float)):
        chips.append(f'<span class="chip">${cost:.2f}</span>')
    a('<div class="chips-row">' + "".join(chips) + "</div>")
    if not result.ok:
        a(f'<div class="warn">Run problem: {esc(result.error or "unknown error")}</div>')

    a("<h3>Who and what</h3><ul class=\"kv\">")
    a(f'<li><b>Persona</b>{esc(persona.name)}: '
      f'{esc(persona.blurb or persona.occupation or persona.id)}</li>')
    dev = persona.device + (f" ({persona.viewport})" if persona.viewport else "")
    a(f'<li><b>Device</b>{esc(dev)} &middot; tech {esc(persona.tech_savvy)} '
      f'&middot; patience {esc(persona.patience)}</li>')
    a(f'<li><b>Task</b>{esc(task.goal)}</li>')
    if task.url:
        a(f'<li><b>Start</b><a href="{esc(task.url)}" target="_blank" rel="noopener">'
          f'{esc(task.url)}</a></li>')
    a("</ul>")

    if report.get("first_impression"):
        a("<h3>First impression</h3><blockquote>" + esc(report["first_impression"]) + "</blockquote>")
    if report.get("in_character_summary"):
        a("<h3>In their words</h3><blockquote>" + esc(report["in_character_summary"]) + "</blockquote>")

    steps = report.get("steps") or []
    if steps:
        a('<h3>Step by step</h3><div class="scroll"><table><thead><tr><th>#</th><th>Tried to</th>'
          "<th>Did</th><th>Expected</th><th>Got</th><th>Felt</th><th>Fric.</th></tr></thead><tbody>")
        for s in steps:
            fr = s.get("friction", 0) or 0
            bar = "●" * fr + "○" * max(0, 3 - fr)
            a("<tr><td class=\"num\">{n}</td><td>{i}</td><td>{d}</td><td>{e}</td>"
              "<td>{g}</td><td>{f}</td><td class=\"num\">{b}</td></tr>".format(
                  n=esc(str(s.get("n", ""))), i=esc(s.get("intent", "")), d=esc(s.get("action", "")),
                  e=esc(s.get("expected", "")), g=esc(s.get("what_happened", "")),
                  f=esc(_feel(s.get("feeling", ""))), b=bar))
        a("</tbody></table></div>")
        thoughts = [s for s in steps if s.get("thought") or s.get("screenshot")]
        if thoughts:
            a('<details><summary>Thinking aloud, with screenshots</summary><div class="think">')
            for s in thoughts:
                if s.get("thought"):
                    a(f'<p><b>{esc(str(s.get("n")))}.</b> {esc(s["thought"])}</p>')
                shot = s.get("screenshot", "")
                if shot and os.path.exists(os.path.join(result.run_dir, shot)):
                    a(f'<img src="{esc(rel + "/" + shot)}" alt="" loading="lazy">')
            a("</div></details>")

    findings = report.get("friction_points") or []
    if findings:
        a("<h3>Friction</h3>")
        for f in findings:
            sev = f.get("severity", "minor")
            a(f'<div class="lf {esc(sev)}"><span class="pill">{esc(sev)}</span>'
              f'<b>{esc(f.get("what") or "(unnamed)")}</b>')
            for label, key in (("Where", "where"), ("Why it hurts", "why_it_hurts"),
                               ("Evidence", "evidence"), ("Suggested fix", "suggested_fix"),
                               ("Heuristic", "heuristic")):
                if f.get(key):
                    a(f'<div class="lfrow"><b>{label}</b> {esc(f[key])}</div>')
            a("</div>")

    for title, key in (("What worked", "delights"), ("Moments of confusion", "confusions"),
                       ("Unmet expectations", "unmet_expectations"),
                       ("Accessibility notes", "accessibility_notes"),
                       ("Technical observations", "technical_observations"),
                       ("Questions for the team", "questions_for_the_team")):
        items = report.get(key) or []
        if items:
            a(f"<h3>{title}</h3><ul>")
            for item in items:
                a(f"<li>{esc(item)}</li>")
            a("</ul>")

    if report.get("one_thing_to_fix"):
        a('<h3>If you fix one thing</h3><p class="one"><b>'
          + esc(report["one_thing_to_fix"]) + "</b></p>")
    if report.get("analyst_summary"):
        a("<h3>Analyst summary</h3><p>" + esc(report["analyst_summary"]) + "</p>")
    return "".join(out)


def render_index_html(results: list[RunResult], study_name: str, meta: dict[str, Any]) -> str:
    esc = html.escape
    totals = {s: 0 for s in SEVERITIES}
    for result in results:
        for sev, n in severity_counts(result.report).items():
            totals[sev] += n
    completed = sum(1 for r in results if r.report.get("outcome") == "completed")
    difficulties = [r.report.get("difficulty") for r in results if r.report.get("difficulty")]
    avg_diff = f"{sum(difficulties) / len(difficulties):.1f}" if difficulties else "-"

    stats = study_stats(results)
    groups = prioritise(results)
    agents = esc(", ".join(sorted({r.spec.agent for r in results})))
    n_sessions = max(1, len(results))

    # ---- shared fragments -------------------------------------------------
    def avatar(persona) -> str:
        return f'<span class="ava" title="{esc(persona.name)}">{persona_icon(persona)}</span>'

    def issue_card(group: dict) -> str:
        sev = group["severity"]
        tags = [
            f'<span class="tag">hit by {group["reach"]}/{group["total_personas"]}</span>',
            f'<span class="tag grade-{group["grade"]}">{group["grade"]}</span>',
            f'<span class="tag">impact {group["impact"]:.0f}</span>',
        ]
        if group["universal"]:
            tags.insert(0, '<span class="tag hot">everyone</span>')
        if group["disputed"]:
            tags.append('<span class="tag">rated ' + esc(" / ".join(group["severities"])) + "</span>")
        if group["named_by"]:
            tags.append('<span class="tag star">&#9733; their one fix</span>')
        return (
            f'<div class="f {sev}"><div class="head">'
            f'<span class="rank">{group["rank"]:02d}</span>'
            f'<span class="what">{_pill(sev)}{esc(group["what"])}</span></div>'
            f'<div class="tags">{"".join(tags)}</div>'
            f'<div class="meta">{esc(", ".join(group["personas"]))}'
            f'{" &middot; " + esc(group["where"]) if group.get("where") else ""}</div>'
            + (f'<div class="fix">{esc(group["why_it_hurts"])}</div>' if group.get("why_it_hurts") else "")
            + (f'<div class="fix"><strong>Fix:</strong> {esc(group["fixes"][0])}</div>'
               if group.get("fixes") else "")
            + (f'<details><summary>evidence</summary><ul>'
               + "".join(f"<li>{esc(e)}</li>" for e in group["evidence"][:4])
               + "</ul></details>" if group.get("evidence") else "")
            + "</div>"
        )

    def dist_bar(pairs: list[tuple[str, int, str]]) -> str:
        """pairs: (css-class, count, label). Renders a stacked bar and a legend."""
        total = sum(c for _, c, _ in pairs) or 1
        segs = "".join(f'<i class="{cls}" style="width:{c / total * 100:.4f}%"></i>'
                       for cls, c, _ in pairs if c)
        leg = "".join(f'<span><i class="{cls}"></i><b>{c}</b> {esc(lbl)}</span>'
                      for cls, c, lbl in pairs if c)
        return f'<div class="dist">{segs}</div><div class="lg">{leg}</div>'

    strips = []  # (persona_first_name, name, [(src, caption)])
    for result in results:
        shots = [
            (os.path.basename(result.run_dir) + "/" + s["screenshot"],
             f'{s.get("n")}. {s.get("action") or s.get("what_happened") or ""}')
            for s in result.report.get("steps") or []
            if s.get("screenshot")
            and os.path.exists(os.path.join(result.run_dir, s["screenshot"]))
        ]
        if shots:
            strips.append((result.spec.persona, shots))

    quotes = [(r.spec.persona, r.report.get("in_character_summary", "")) for r in results]
    quotes = [q for q in quotes if q[1]]
    delights = [(r.spec.persona.name, d) for r in results for d in (r.report.get("delights") or [])]

    outcome_order = ["completed", "partial", "abandoned", "failed", "unknown"]
    oc: dict[str, int] = {}
    for r in results:
        o = r.report.get("outcome") or "unknown"
        oc[o if o in outcome_order else "unknown"] = oc.get(o if o in outcome_order else "unknown", 0) + 1

    logdocs: list[tuple[str, str, str]] = []  # (log_id, title, html)

    parts = [_HTML_HEAD.replace("__TITLE__", esc(study_name))]
    add = parts.append
    add('<div class="grain"></div>')

    # ---- sidebar ----------------------------------------------------------
    nav = [("overview", "Overview", ICON_GRID, None),
           ("sessions", "Sessions", ICON_ROWS, len(results)),
           ("issues", "Issues", ICON_FLAG, len(groups))]
    if strips:
        nav.append(("gallery", "Gallery", ICON_IMAGE, sum(len(s[1]) for s in strips)))
    if quotes or delights:
        nav.append(("voices", "Voices", ICON_QUOTE, None))

    add('<div class="app"><aside class="side"><div class="side-top">')
    add(f'<div class="brand"><span class="mark">{LOGO_MARK}</span>'
        '<span class="word">uxprobe<span> · usability</span></span></div>')
    add(f'<button class="side-toggle" type="button" aria-label="Collapse sidebar" '
        f'title="Collapse sidebar">{ICON_SIDEBAR}</button>')
    add("</div>")
    add('<div class="navlabel">Study</div><nav class="nav">')
    for vid, label, icon, count in nav:
        badge = f'<span class="n">{count}</span>' if count is not None else ""
        add(f'<a data-view="{vid}" href="#{vid}" title="{esc(label)}">'
            f'{icon}<span>{label}</span>{badge}</a>')
    add("</nav>")
    add('<div class="foot"><div class="name">' + esc(study_name) + "</div>"
        f'<div class="row"><span>Run</span><span>{esc(meta.get("started_at", "")[:10])}</span></div>'
        f'<div class="row"><span>Sessions</span><span>{len(results)}</span></div>'
        f'<div class="row"><span>Agent</span><span>{agents}</span></div>'
        f'<div class="row"><span>Findings</span><span>{stats["issues"]} merged</span></div>'
        "</div>")
    add("</aside>")

    # ---- main -------------------------------------------------------------
    add('<main class="main"><div class="topbar"><div class="crumb">'
        'uxprobe<span class="sep">/</span><b>' + esc(study_name) + "</b>"
        '<span class="sep">/</span><span>simulated usability</span></div></div>'
        '<div class="content">')

    # Overview -------------------------------------------------------------
    add('<section class="view" id="overview"><div class="vhead">'
        "<h1>Overview</h1><p>A moderated usability test where each participant is a coding "
        "agent playing a character. Mechanical observations are reliable; feelings are "
        "hypotheses to check with real people.</p></div>")
    add('<div class="kpis">')
    add(f'<div class="kpi"><div class="k">Fix first</div>'
        f'<div class="v blocker" data-count="{stats["fix_first"]}">{stats["fix_first"]}</div>'
        f'<div class="note">of {stats["issues"]} merged issues</div></div>')
    add(f'<div class="kpi"><div class="k">Completed</div>'
        f'<div class="v ok"><span data-count="{completed}">{completed}</span>'
        f'<small>/{n_sessions}</small></div>'
        f'<div class="note">tasks finished</div></div>')
    add(f'<div class="kpi"><div class="k">Measured</div>'
        f'<div class="v accent" data-count="{stats["measured"]}">{stats["measured"]}</div>'
        f'<div class="note">checked in the page</div></div>')
    add(f'<div class="kpi"><div class="k">Hit everyone</div>'
        f'<div class="v" data-count="{stats["universal"]}">{stats["universal"]}</div>'
        f'<div class="note">issues all personas met</div></div>')
    add("</div>")
    add('<div class="panel"><div class="ph"><h3>Outcomes</h3>'
        f'<span class="sub">{len(results)} sessions</span></div><div class="pb">')
    add(dist_bar([(f"seg-{k}", oc.get(k, 0), k) for k in outcome_order]))
    add("</div></div>")
    if sum(totals.values()):
        add('<div class="panel"><div class="ph"><h3>Findings by severity</h3>'
            f'<span class="sub">{stats["issues"]} merged</span></div><div class="pb">')
        add(dist_bar([(f"sev-{s}", totals[s], s) for s in SEVERITIES]))
        add("</div></div>")
    if groups:
        add('<div class="panel"><div class="ph"><h3>Top of the list</h3>'
            '<span class="sub">highest impact first</span></div><div class="pb">')
        for group in groups[:3]:
            add(issue_card(group))
        add('<p style="margin-top:12px"><a data-view="issues" href="#issues">'
            f'See all {len(groups)} issues &rarr;</a></p>')
        add("</div></div>")
    add("</section>")

    # Sessions -------------------------------------------------------------
    add('<section class="view" id="sessions"><div class="vhead">'
        "<h1>Sessions</h1><p>One row per participant. &ldquo;Ease&rdquo; is the "
        "participant's own score and is a feeling, not a measurement; treat it as a "
        "hint, not a metric.</p></div>")
    add('<div class="panel"><div class="scroll"><table><thead><tr>'
        "<th>Persona</th><th>Task</th><th>Outcome</th><th>Diff.</th><th>Ease</th>"
        "<th>Blockers</th><th>One thing to fix</th><th></th></tr></thead><tbody>")
    for i, result in enumerate(results):
        report = result.report
        counts = severity_counts(report)
        log_id = f"log-{i}"
        logdocs.append((log_id,
                        f"{result.spec.persona.name} · {result.spec.task.title}",
                        render_session_html(result, esc)))
        outcome = report.get("outcome", "unknown")
        name = result.spec.persona.name
        ease = report.get("ease_score")
        if ease is None or ease == "":
            ease_cell = '<span class="zero">n/a</span>'
        else:
            try:
                pct = max(0, min(100, int(ease)))
            except (TypeError, ValueError):
                pct = 0
            ease_cell = (f'<span class="meter"><span class="track">'
                         f'<span class="fill" style="width:{pct}%"></span></span>{esc(_fmt(ease))}</span>')
        blockers = counts["blocker"]
        block_cell = f'<span class="bnum">{blockers}</span>' if blockers else '<span class="zero">0</span>'
        add(
            f'<tr><td><div class="who">{avatar(result.spec.persona)}'
            f'<span><span class="nm">{esc(name)}</span><br>'
            f'<span class="dev">{esc(result.spec.persona.device)}</span></span></div></td>'
            f"<td>{esc(result.spec.task.title)}</td>"
            f'<td><span class="badge {esc(outcome)}"><span class="st"></span>{esc(outcome)}</span></td>'
            f'<td class="num">{esc(_fmt(report.get("difficulty")))}</td>'
            f"<td>{ease_cell}</td>"
            f'<td class="num">{block_cell}</td>'
            f'<td class="fixcell">{esc(report.get("one_thing_to_fix", ""))}</td>'
            f'<td><button class="linklog" type="button" data-log="{log_id}">log</button></td></tr>'
        )
    add("</tbody></table></div></div></section>")

    # Issues ---------------------------------------------------------------
    add('<section class="view" id="issues"><div class="vhead">'
        "<h1>What to fix</h1><p>Duplicate reports of one problem are merged into a single "
        "issue. &ldquo;Hit by&rdquo; counts distinct participants; &ldquo;measured&rdquo; "
        "means it was checked in the page rather than felt.</p></div>")
    if groups:
        for band, label in ((BAND_FIX_FIRST, "Fix first"), (BAND_NEXT, "Next"),
                            (BAND_BACKLOG, "Backlog")):
            band_groups = [g for g in groups if g["band"] == band]
            if not band_groups:
                continue
            add(f'<div class="band">{label} <span class="count">{len(band_groups)}</span></div>')
            for group in band_groups:
                add(issue_card(group))
    else:
        add('<div class="empty">No issues were merged from these sessions.</div>')
    add("</section>")

    # Gallery --------------------------------------------------------------
    if strips:
        add('<section class="view" id="gallery"><div class="vhead">'
            "<h1>Gallery</h1><p>Every participant screenshots each meaningful step, wired to "
            "the moment that produced it. Click a frame to open it full size.</p></div>")
        for persona, shots in strips:
            add(f'<div class="gal"><h4>{avatar(persona)}{esc(persona.name)}</h4><div class="strip">')
            for src, caption in shots:
                add(f'<figure><a href="{esc(src)}" target="_blank" rel="noopener">'
                    f'<img src="{esc(src)}" alt="{esc(caption)}" loading="lazy"></a>'
                    f"<figcaption>{esc(caption)}</figcaption></figure>")
            add("</div></div>")
        add("</section>")

    # Voices ---------------------------------------------------------------
    if quotes or delights:
        add('<section class="view" id="voices"><div class="vhead">'
            "<h1>Voices</h1><p>In-character summaries and the things that genuinely worked. "
            "Useful colour, not evidence.</p></div>")
        for persona, quote in quotes:
            add(f'<div class="quote"><p>{esc(quote)}</p>'
                f'<div class="cite">{avatar(persona)}{esc(persona.name)}</div></div>')
        if delights:
            add('<div class="band" style="margin-top:22px">What worked '
                f'<span class="count">{len(delights)}</span></div><ul class="worked">')
            for who, item in delights:
                add(f'<li>{esc(item)} <span class="by">({esc(who)})</span></li>')
            add("</ul>")
        add("</section>")

    add('<div class="foot">These are simulated participants driven by a coding agent, not real '
        "users. Mechanical observations, like a control that does not respond, an unlabelled input "
        "or a console error, are reliable and worth acting on. Statements about how someone "
        "feels are hypotheses to check with real people, not measurements.</div>")
    add("</div></main></div>")

    # hidden session documents + modal shell (log opens here, formatted)
    for log_id, title, doc in logdocs:
        add(f'<div class="logsrc" id="{log_id}" data-title="{esc(title)}" hidden>{doc}</div>')
    add('<div class="modal" id="logmodal" role="dialog" aria-modal="true" aria-hidden="true">'
        '<div class="modal-card"><div class="modal-head"><span class="t"></span>'
        f'<button class="modal-close" type="button" aria-label="Close">{ICON_X}</button></div>'
        '<div class="modal-body logdoc"></div></div></div>')

    add(_HTML_TAIL_JS)
    add("</body></html>")
    return "\n".join(parts)


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
