"""The self-contained HTML dashboard for a study.

One file per study, no build step, works from ``file://``. The page is an
app shell (sidebar + views) with a session replay, a journey map, a
who-hit-what matrix, a filterable issue list, a gallery and the voices.
Everything is progressive enhancement: without JavaScript every view is
shown stacked and the report still reads top to bottom.
"""

from __future__ import annotations

import html
import json
import os
from typing import Any

from .analysis import (
    BAND_BACKLOG,
    BAND_FIX_FIRST,
    BAND_NEXT,
    MEASURED,
    OBSERVED,
    IMPRESSION,
    issue_ticket,
    prioritise,
    study_stats,
)
from .dashboard_css import DASHBOARD_CSS
from .dashboard_js import DASHBOARD_JS
from .models import RunResult, SEVERITIES, severity_counts

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


def _first_name(name: str) -> str:
    return (name or "").split(",")[0].split(" the ")[0].strip() or name


def _duration(seconds: float) -> str:
    seconds = int(round(seconds or 0))
    if seconds < 60:
        return f"{seconds}s"
    return f"{seconds // 60}m {seconds % 60:02d}s"


# --------------------------------------------------------------------------
# icons: Phosphor (https://phosphoricons.com) filled glyphs inlined for the
# navigation and personas, plus a few stroke glyphs drawn to match, so the
# report stays self-contained and works offline.
# --------------------------------------------------------------------------


def _icon(path: str) -> str:
    return (f'<svg class="ic" viewBox="0 0 256 256" fill="currentColor" aria-hidden="true">'
            f'{path}</svg>')


def _sicon(inner: str, cls: str = "ic") -> str:
    return (f'<svg class="{cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
            f'{inner}</svg>')


ICON_GRID = _icon('<path d="M104,40H56A16,16,0,0,0,40,56v48a16,16,0,0,0,16,16h48a16,16,0,0,0,16-16V56A16,16,0,0,0,104,40Zm0,64H56V56h48v48Zm96-64H152a16,16,0,0,0-16,16v48a16,16,0,0,0,16,16h48a16,16,0,0,0,16-16V56A16,16,0,0,0,200,40Zm0,64H152V56h48v48Zm-96,32H56a16,16,0,0,0-16,16v48a16,16,0,0,0,16,16h48a16,16,0,0,0,16-16V152A16,16,0,0,0,104,136Zm0,64H56V152h48v48Zm96-64H152a16,16,0,0,0-16,16v48a16,16,0,0,0,16,16h48a16,16,0,0,0,16-16V152A16,16,0,0,0,200,136Zm0,64H152V152h48v48Z"/>')
ICON_ROWS = _icon('<path d="M80,64a8,8,0,0,1,8-8H216a8,8,0,0,1,0,16H88A8,8,0,0,1,80,64Zm136,56H88a8,8,0,0,0,0,16H216a8,8,0,0,0,0-16Zm0,64H88a8,8,0,0,0,0,16H216a8,8,0,0,0,0-16ZM44,52A12,12,0,1,0,56,64,12,12,0,0,0,44,52Zm0,64a12,12,0,1,0,12,12A12,12,0,0,0,44,116Zm0,64a12,12,0,1,0,12,12A12,12,0,0,0,44,180Z"/>')
ICON_FLAG = _icon('<path d="M242.63,96.44l-184-64A8,8,0,0,0,48,40V216a8,8,0,0,0,16,0V173.69l178.63-62.13a8,8,0,0,0,0-15.12ZM64,156.75V51.25L215.65,104Z"/>')
ICON_IMAGE = _icon('<path d="M208,32H48A16,16,0,0,0,32,48V208a16,16,0,0,0,16,16H208a16,16,0,0,0,16-16V48A16,16,0,0,0,208,32ZM48,48H208v77.38l-24.69-24.7a16,16,0,0,0-22.62,0L53.37,208H48ZM208,208H76l96-96,36,36v60ZM96,120A24,24,0,1,0,72,96,24,24,0,0,0,96,120Zm0-32a8,8,0,1,1-8,8A8,8,0,0,1,96,88Z"/>')
ICON_QUOTE = _icon('<path d="M100,56H40A16,16,0,0,0,24,72v64a16,16,0,0,0,16,16h60v8a32,32,0,0,1-32,32,8,8,0,0,0,0,16,48.05,48.05,0,0,0,48-48V72A16,16,0,0,0,100,56Zm0,80H40V72h60ZM216,56H156a16,16,0,0,0-16,16v64a16,16,0,0,0,16,16h60v8a32,32,0,0,1-32,32,8,8,0,0,0,0,16,48.05,48.05,0,0,0,48-48V72A16,16,0,0,0,216,56Zm0,80H156V72h60Z"/>')
ICON_X = _icon('<path d="M205.66,194.34a8,8,0,0,1-11.32,11.32L128,139.31,61.66,205.66a8,8,0,0,1-11.32-11.32L116.69,128,50.34,61.66A8,8,0,0,1,61.66,50.34L128,116.69l66.34-66.35a8,8,0,0,1,11.32,11.32L139.31,128Z"/>')
ICON_SIDEBAR = _icon('<path d="M216,40H40A16,16,0,0,0,24,56V200a16,16,0,0,0,16,16H216a16,16,0,0,0,16-16V56A16,16,0,0,0,216,40ZM40,56H80V200H40ZM216,200H96V56H216V200Z"/>')
ICON_FILM = _sicon('<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18M3 15h18M8 4v16M16 4v16"/>')
ICON_SEARCH = _sicon('<circle cx="11" cy="11" r="6.5"/><path d="M16 16l4.5 4.5"/>')
ICON_SUN = _sicon('<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.3 5.3l1.4 1.4M17.3 17.3l1.4 1.4M5.3 18.7l1.4-1.4M17.3 6.7l1.4-1.4"/>', "ic sun")
ICON_MOON = _sicon('<path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a7.5 7.5 0 1 0 10.5 10.5z"/>', "ic moon")
ICON_HELP = _sicon('<circle cx="12" cy="12" r="9"/><path d="M9.6 9.6a2.5 2.5 0 1 1 3.4 2.3c-.7.4-1 1-1 1.7v.4"/><circle cx="12" cy="17" r=".6" fill="currentColor"/>')
ICON_EXPORT = _sicon('<path d="M12 4v11M7.5 10.5L12 15l4.5-4.5M4 19h16"/>')
ICON_PLAY = _sicon('<path d="M8 5.5v13l11-6.5z" fill="currentColor"/>', "ic play")
ICON_PAUSE = _sicon('<path d="M7 5h3.5v14H7zM13.5 5H17v14h-3.5z" fill="currentColor" stroke="none"/>', "ic pause")
ICON_FIRST = _sicon('<path d="M6 5v14"/><path d="M18 6.5v11L9 12z" fill="currentColor"/>')
ICON_LAST = _sicon('<path d="M18 5v14"/><path d="M6 6.5v11L15 12z" fill="currentColor"/>')
ICON_LEFT = _sicon('<path d="M15 5l-7 7 7 7"/>')
ICON_RIGHT = _sicon('<path d="M9 5l7 7-7 7"/>')
ICON_COPY = _sicon('<rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V6a2 2 0 0 1 2-2h9"/>')
ICON_OUT = _sicon('<path d="M7 17L17 7M9 7h8v8"/>')
ICON_DOC = _sicon('<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h6"/>')

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


def _pill(sev: str) -> str:
    return f'<span class="pill {sev}">{sev}</span>'


# --------------------------------------------------------------------------
# per-session document (the "log" modal)
# --------------------------------------------------------------------------


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
             f'<span class="chip">{_duration(result.duration_s)}</span>']
    turns = result.agent_meta.get("num_turns")
    cost = result.agent_meta.get("total_cost_usd")
    if turns:
        chips.append(f'<span class="chip">{turns} turns</span>')
    if isinstance(cost, (int, float)):
        chips.append(f'<span class="chip">${cost:.2f}</span>')
    chips.append(f'<a class="chip" href="{esc(rel)}/report.md" title="the Markdown report on disk">report.md &nearr;</a>')
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
            a(f'<div class="lf {esc(sev)}">{_pill(esc(sev))}'
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


# --------------------------------------------------------------------------
# the study dashboard
# --------------------------------------------------------------------------

_HEAD = """<!doctype html>
<html lang="en" class="no-js"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>uxprobe · __TITLE__</title>
<script>try{document.documentElement.className="js";var t=localStorage.getItem("uxprobe-theme");if(t==="light"||t==="dark"){document.documentElement.setAttribute("data-theme",t);}}catch(e){}</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Schibsted+Grotesk:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;600;700&display=swap" rel="stylesheet">
<style>__CSS__</style></head><body>
"""

_OUTCOME_ORDER = ["completed", "partial", "abandoned", "failed", "unknown"]
_OUTCOME_WORD = {"completed": "finished", "partial": "got part of the way", "abandoned": "gave up",
                 "failed": "failed", "unknown": "unclear"}


def _ease_class(ease: Any) -> str:
    try:
        pct = int(ease)
    except (TypeError, ValueError):
        return ""
    return "low" if pct < 40 else ("mid" if pct < 70 else "high")


def _meter(ease: Any, esc=html.escape) -> str:
    if ease is None or ease == "":
        return '<span class="zero">n/a</span>'
    try:
        pct = max(0, min(100, int(ease)))
    except (TypeError, ValueError):
        pct = 0
    return (f'<span class="meter {_ease_class(ease)}" title="ease {pct}/100, the participant\'s own score">'
            f'<span class="track"><span class="fill" style="width:{pct}%"></span></span>{esc(_fmt(ease))}</span>')


def render_index_html(results: list[RunResult], study_name: str, meta: dict[str, Any]) -> str:
    esc = html.escape
    totals = {s: 0 for s in SEVERITIES}
    for result in results:
        for sev, n in severity_counts(result.report).items():
            totals[sev] += n
    completed = sum(1 for r in results if r.report.get("outcome") == "completed")
    stats = study_stats(results)
    groups = prioritise(results)
    agents = esc(", ".join(sorted({r.spec.agent for r in results})))
    n_sessions = max(1, len(results))
    study_dir = os.path.dirname(os.path.abspath(results[0].run_dir)) if results else ""

    # ---- per-session data, shared by the journey map, replay, gallery -----
    sessions: list[dict[str, Any]] = []
    for i, result in enumerate(results):
        report = result.report or {}
        rel = os.path.basename(result.run_dir)
        steps = []
        for s in report.get("steps") or []:
            shot = s.get("screenshot") or ""
            if shot and not os.path.exists(os.path.join(result.run_dir, shot)):
                shot = ""
            steps.append({
                "n": s.get("n"), "intent": s.get("intent", ""), "action": s.get("action", ""),
                "expected": s.get("expected", ""), "what": s.get("what_happened", ""),
                "feeling": s.get("feeling", ""), "friction": int(s.get("friction") or 0),
                "thought": s.get("thought", ""), "shot": shot,
            })
        sessions.append({
            "i": i, "name": result.spec.persona.name, "first": _first_name(result.spec.persona.name),
            "persona_id": result.spec.persona.id, "device": result.spec.persona.device,
            "task": result.spec.task.title, "outcome": report.get("outcome") or "unknown",
            "ease": report.get("ease_score"), "difficulty": report.get("difficulty"),
            "duration": result.duration_s, "icon": persona_icon(result.spec.persona),
            "dir": rel, "log": f"log-{i}", "agent": result.spec.agent, "ok": result.ok,
            "error": result.error or "", "steps": steps, "result": result,
        })
    total_steps = sum(len(s["steps"]) for s in sessions)
    total_shots = sum(1 for s in sessions for st in s["steps"] if st["shot"])
    max_steps = max((len(s["steps"]) for s in sessions), default=0)
    with_shots = [s for s in sessions if any(st["shot"] for st in s["steps"])]
    with_steps = [s for s in sessions if s["steps"]]

    # ---- shared fragments -------------------------------------------------
    def avatar(persona, cls: str = "") -> str:
        return f'<span class="ava {cls}" title="{esc(persona.name)}">{persona_icon(persona)}</span>'

    def outcome_badge(outcome: str) -> str:
        return f'<span class="badge {esc(outcome)}"><span class="st"></span>{esc(outcome)}</span>'

    persona_by_name = {}
    for r in results:
        persona_by_name.setdefault(r.spec.persona.name, r.spec.persona)

    def issue_card(group: dict, compact: bool = False) -> str:
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
        who = "".join(
            f'<span class="ava" title="{esc(name)}: {esc(rating)}">'
            f'{persona_icon(persona_by_name[name]) if name in persona_by_name else _PERSONA_GLYPHS["_default"]}'
            f'<i class="{esc(rating)}"></i></span>'
            for name, rating in group["by_persona"].items()
        )
        pids = " ".join(sorted({persona_by_name[n].id for n in group["personas"] if n in persona_by_name}))
        text = " ".join([group["what"], group.get("where", ""), group.get("why_it_hurts", ""),
                         " ".join(group.get("fixes", [])), " ".join(group["personas"]),
                         sev, group["grade"], group["band"]]).lower()
        ticket = issue_ticket(group)
        return (
            f'<div class="f {sev}" data-rank="{group["rank"]}" data-sev="{sev}" data-grade="{group["grade"]}" '
            f'data-band="{esc(group["band"])}" data-personas="{esc(pids)}" data-impact="{group["impact"]}" '
            f'data-reach="{group["agreeing"]}" data-text="{esc(text)}">'
            f'<div class="head"><span class="rank">{group["rank"]:02d}</span>'
            f'<span class="what">{_pill(sev)}{esc(group["what"])}</span>'
            f'<button class="abtn copy" type="button" title="Copy as a ticket (Markdown)" '
            f'data-ticket="{esc(ticket)}">{ICON_COPY}ticket</button></div>'
            f'<div class="tags">{"".join(tags)}</div>'
            f'<div class="who-row">{who}<span class="lbl">{esc(", ".join(_first_name(n) for n in group["personas"]))}'
            f'{" &middot; " + esc(group["where"]) if group.get("where") else ""}</span></div>'
            + (f'<div class="fix">{esc(group["why_it_hurts"])}</div>' if group.get("why_it_hurts") and not compact else "")
            + (f'<div class="fix"><strong>Fix:</strong> {esc(group["fixes"][0])}</div>'
               if group.get("fixes") else "")
            + (f'<details class="ev"><summary>evidence</summary><ul>'
               + "".join(f"<li>{esc(e)}</li>" for e in group["evidence"][:4])
               + "</ul></details>" if group.get("evidence") and not compact else "")
            + "</div>"
        )

    def dist_bar(pairs: list[tuple[str, int, str]]) -> str:
        total = sum(c for _, c, _ in pairs) or 1
        segs = "".join(f'<i class="{cls}" style="width:{c / total * 100:.4f}%"></i>'
                       for cls, c, _ in pairs if c)
        leg = "".join(f'<span><i class="{cls}"></i><b>{c}</b> {esc(lbl)}</span>'
                      for cls, c, lbl in pairs if c)
        return f'<div class="dist">{segs}</div><div class="lg">{leg}</div>'

    def spark(steps: list[dict]) -> str:
        if not steps:
            return '<span class="zero">-</span>'
        return ('<span class="spark" title="friction per step">'
                + "".join(f'<i class="fr{s["friction"]}"></i>' for s in steps[:40]) + "</span>")

    oc: dict[str, int] = {}
    for s in sessions:
        key = s["outcome"] if s["outcome"] in _OUTCOME_ORDER else "unknown"
        oc[key] = oc.get(key, 0) + 1

    quotes = [s for s in sessions if s["result"].report.get("in_character_summary")]
    impressions = [s for s in sessions if s["result"].report.get("first_impression")]
    delights = [(s["name"], d) for s in sessions for d in (s["result"].report.get("delights") or [])]

    logdocs: list[tuple[str, str, str]] = []

    parts = [_HEAD.replace("__TITLE__", esc(study_name)).replace("__CSS__", DASHBOARD_CSS)]
    add = parts.append
    add('<div class="grain"></div>')

    # ---- sidebar ----------------------------------------------------------
    nav = [("overview", "Overview", ICON_GRID, None),
           ("sessions", "Sessions", ICON_ROWS, len(results)),
           ("replay", "Replay", ICON_FILM, total_shots or None),
           ("issues", "Issues", ICON_FLAG, len(groups))]
    if with_shots:
        nav.append(("gallery", "Gallery", ICON_IMAGE, total_shots))
    if quotes or delights or impressions:
        nav.append(("voices", "Voices", ICON_QUOTE, None))

    add('<div class="app"><aside class="side"><div class="side-top">')
    add(f'<div class="brand"><span class="mark">{LOGO_MARK}</span>'
        '<span class="word">uxprobe<span> · usability</span></span></div>')
    add(f'<button class="side-toggle" type="button" aria-label="Collapse sidebar" '
        f'title="Collapse sidebar  [">{ICON_SIDEBAR}</button>')
    add("</div>")
    add('<div class="navlabel">Study</div><nav class="nav">')
    for k, (vid, label, icon, count) in enumerate(nav, start=1):
        badge = f'<span class="n">{count}</span>' if count is not None else f'<span class="k"><kbd>{k}</kbd></span>'
        add(f'<a data-view="{vid}" href="#{vid}" title="{esc(label)}  ({k})">'
            f'{icon}<span class="lbl">{label}</span>{badge}</a>')
    add("</nav>")
    if sessions:
        add('<div class="navlabel">Participants</div><nav class="nav pl">')
        for s in sessions:
            add(f'<a class="pp" href="#replay/{s["i"]}/0" data-replay="{s["i"]}:0" title="Replay {esc(s["name"])}">'
                f'<span class="ava">{s["icon"]}</span><span class="nm">{esc(s["first"])}</span>'
                f'<span class="st {esc(s["outcome"])}" title="{esc(s["outcome"])}"></span></a>')
        add("</nav>")
    add('<div class="foot"><div class="name">' + esc(study_name) + "</div>"
        f'<div class="row"><span>Run</span><span>{esc(meta.get("started_at", "")[:10])}</span></div>'
        f'<div class="row"><span>Sessions</span><span>{len(results)}</span></div>'
        f'<div class="row"><span>Agent</span><span>{agents}</span></div>'
        f'<div class="row"><span>Findings</span><span>{stats["issues"]} merged</span></div>'
        f'<div class="row"><span>Agent time</span><span>{stats["minutes"]} min</span></div>'
        "</div>")
    add("</aside>")

    # ---- top bar ----------------------------------------------------------
    add('<main class="main"><div class="topbar"><div class="crumb">'
        'uxprobe<span class="sep">/</span><b>' + esc(study_name) + "</b>"
        '<span class="sep">/</span><span>simulated usability</span></div>')
    add('<div class="tb-right">')
    add(f'<label class="search" title="Search issues  (/)">{ICON_SEARCH}'
        '<input id="q" type="search" placeholder="Search issues" autocomplete="off" spellcheck="false"><kbd>/</kbd></label>')
    exports = [("index.md", "Report as Markdown"), ("issues.md", "Tickets, ready to paste"),
               ("issues.csv", "Issues as CSV"), ("summary.json", "Everything, machine-readable"),
               ("findings.md", "Agent-written findings memo")]
    exports = [(f, d) for f, d in exports if study_dir and os.path.exists(os.path.join(study_dir, f))]
    if exports:
        add(f'<details class="menu"><summary class="tbtn" title="Files on disk next to this page">{ICON_EXPORT}Files</summary><div class="dd">')
        for fname, desc in exports:
            size = os.path.getsize(os.path.join(study_dir, fname))
            add(f'<a href="{esc(fname)}" target="_blank" rel="noopener">{ICON_DOC}<span>{esc(desc)}</span>'
                f'<small>{esc(fname)} · {size / 1024:.0f} KB</small></a>')
        add("</div></details>")
    add(f'<button class="tbtn" id="theme" type="button" title="Toggle light / dark  (t)">{ICON_SUN}{ICON_MOON}</button>')
    add(f'<button class="tbtn" type="button" data-help title="Keyboard shortcuts  (?)">{ICON_HELP}</button>')
    add('</div></div><div class="content">')

    # ---- Overview -----------------------------------------------------------
    top = groups[0] if groups else None
    lead = (f'<span class="num">{len(results)}</span> simulated participant{"s" if len(results) != 1 else ""} '
            f'took <span class="num">{total_steps}</span> steps and <span class="num">{total_shots}</span> screenshots '
            f'in <span class="num">{stats["minutes"]}</span> minutes of agent time. ')
    if results:
        lead += f'<b>{completed} of {n_sessions}</b> finished the task. '
    if top:
        lead += f'Top of the list: <span class="fr">{esc(top["what"])}</span>'
    add('<section class="view" id="overview"><div class="vhead"><div>'
        '<div class="eyebrow"><i></i>Study &middot; ' + esc(meta.get("started_at", "")[:10]) + "</div>"
        "<h1>Overview</h1>"
        f'<p class="lead">{lead}</p></div>'
        '<div class="right"><a class="abtn pri" data-view="replay" href="#replay">' + ICON_PLAY + " Watch the sessions</a></div></div>")
    add('<div class="kpis">')
    add(f'<div class="kpi"><div class="k">Fix first</div>'
        f'<div class="v blocker" data-count="{stats["fix_first"]}">{stats["fix_first"]}</div>'
        f'<div class="note">blockers and agreed-on pain</div></div>')
    add(f'<div class="kpi"><div class="k">Completed</div>'
        f'<div class="v ok"><span data-count="{completed}">{completed}</span>'
        f'<small>/{n_sessions}</small></div>'
        f'<div class="note">tasks finished</div></div>')
    add(f'<div class="kpi"><div class="k">Issues</div>'
        f'<div class="v" data-count="{stats["issues"]}">{stats["issues"]}</div>'
        f'<div class="note">merged from {stats["raw_findings"]} raw findings</div></div>')
    add(f'<div class="kpi"><div class="k">Measured</div>'
        f'<div class="v accent" data-count="{stats["measured"]}">{stats["measured"]}</div>'
        f'<div class="note">checked in the page, not felt</div></div>')
    add(f'<div class="kpi"><div class="k">Hit everyone</div>'
        f'<div class="v" data-count="{stats["universal"]}">{stats["universal"]}</div>'
        f'<div class="note">issues every persona met</div></div>')
    add("</div>")

    # journey map
    if with_steps:
        add('<div class="panel"><div class="ph"><h3>Journey map</h3>'
            '<span class="sub">friction at every step, one row per participant</span>'
            '<span class="right">hover a step for the thought, click to replay it</span></div><div class="pb">')
        add(f'<div class="jm" style="--n:{max_steps}"><div class="jm-head"><div>Participant</div>')
        ticks = []
        every = 10 if max_steps > 30 else (5 if max_steps > 12 else 1)
        for k in range(1, max_steps + 1):
            left = f"{(k - 0.5) / max_steps * 100:.3f}%"
            major = k == 1 or k % every == 0 or k == max_steps
            ticks.append(f'<i class="{"maj" if major else ""}" style="left:{left}"></i>')
            if major:
                ticks.append(f'<b style="left:{left}">{k}</b>')
        add(f'<div class="jm-axis">{"".join(ticks)}</div><div class="tl">Ease &middot; time</div></div>')
        for s in sessions:
            add('<div class="jm-row">')
            add(f'<div class="jm-who"><span class="ava">{s["icon"]}</span><span style="min-width:0">'
                f'<div class="nm">{esc(s["first"])}</div><div class="sub"><span class="st {esc(s["outcome"])}" '
                f'style="width:6px;height:6px;border-radius:99px;display:inline-block"></span>{esc(s["outcome"])} &middot; {esc(s["device"])}</div></span></div>')
            if s["steps"]:
                cells = "".join(
                    f'<button class="jm-cell fr{st["friction"]}{" shot" if st["shot"] else ""}" type="button" '
                    f'style="--i:{k}" data-s="{s["i"]}" data-i="{k}" aria-label="Step {st["n"]}: {esc(st["intent"] or st["action"])}"></button>'
                    for k, st in enumerate(s["steps"]))
                add(f'<div class="jm-strip">{cells}</div>')
            else:
                add(f'<div class="jm-empty">no step log{": " + esc(s["error"][:60]) if s["error"] else ""}</div>')
            add(f'<div class="jm-tail">{_meter(s["ease"])}<span class="dur">{_duration(s["duration"])}</span></div>')
            add("</div>")
        add("</div>")
        add('<div class="jm-legend"><span><i></i>smooth</span><span><i class="fr1"></i>a snag</span>'
            '<span><i class="fr2"></i>real friction</span><span><i class="fr3"></i>stuck</span>'
            '<span><i style="background:transparent;border:1px dashed var(--faint);position:relative"></i>dot = screenshot taken</span>'
            '<span class="hint">ease is the participant\'s own 0 to 100 score</span></div>')
        add("</div></div>")

    add('<div class="grid2">')
    add('<div class="panel"><div class="ph"><h3>Outcomes</h3>'
        f'<span class="sub">{len(results)} sessions</span></div><div class="pb">')
    add(dist_bar([(f"seg-{k}", oc.get(k, 0), _OUTCOME_WORD[k]) for k in _OUTCOME_ORDER]))
    add("</div></div>")
    add('<div class="panel"><div class="ph"><h3>Findings by severity</h3>'
        f'<span class="sub">{stats["raw_findings"]} raw, {stats["issues"]} after merging</span></div><div class="pb">')
    if sum(totals.values()):
        add(dist_bar([(f"sev-{s}", totals[s], s) for s in SEVERITIES]))
    else:
        add('<div class="empty">No findings were reported.</div>')
    add("</div></div></div>")

    # who hit what
    personas_cols = []
    seen_names = set()
    for r in results:
        if r.spec.persona.name not in seen_names:
            seen_names.add(r.spec.persona.name)
            personas_cols.append(r.spec.persona)
    matrix_rows = [g for g in groups if g["band"] != BAND_BACKLOG][:12] or groups[:8]
    if matrix_rows and len(personas_cols) > 1:
        add('<div class="panel"><div class="ph"><h3>Who hit what</h3>'
            '<span class="sub">each participant\'s own rating of the top issues</span>'
            '<span class="right"><span class="lg" style="margin:0"><span><i class="sev-blocker"></i>blocker</span>'
            '<span><i class="sev-major"></i>major</span><span><i class="sev-minor"></i>minor</span>'
            '<span><i class="sev-nitpick"></i>nitpick</span></span></span></div><div class="scroll">')
        add('<table class="mx"><thead><tr><th>Issue</th>')
        for p in personas_cols:
            add(f'<th class="p"><span class="ava">{persona_icon(p)}</span><span>{esc(_first_name(p.name))}</span></th>')
        add('<th style="text-align:right">Impact</th></tr></thead><tbody>')
        for g in matrix_rows:
            add(f'<tr><td class="w"><span class="rk">{g["rank"]:02d}</span>{_pill(g["severity"])}'
                f'<span class="txt" title="{esc(g["what"])}">{esc(g["what"])}</span></td>')
            for p in personas_cols:
                rating = g["by_persona"].get(p.name)
                if rating:
                    add(f'<td class="c"><i class="{esc(rating)}" title="{esc(_first_name(p.name))}: {esc(rating)}"></i></td>')
                else:
                    add('<td class="c"><i class="none"></i></td>')
            add(f'<td class="r">{g["impact"]:.0f}</td></tr>')
        add("</tbody></table></div>")
        rest = len(groups) - len(matrix_rows)
        if rest > 0:
            add(f'<div class="pb" style="padding-top:10px;color:var(--muted);font-size:.78rem">'
                f'{rest} more in the <a data-view="issues" href="#issues">full list</a>.</div>')
        add("</div>")

    if groups:
        add('<div class="panel"><div class="ph"><h3>Top of the list</h3>'
            '<span class="sub">highest impact first</span></div><div class="pb">')
        for group in groups[:3]:
            add(issue_card(group))
        add('<p style="margin-top:12px"><a data-view="issues" href="#issues">'
            f'See all {len(groups)} issues &rarr;</a></p>')
        add("</div></div>")
    add("</section>")

    # ---- Sessions -----------------------------------------------------------
    add('<section class="view" id="sessions"><div class="vhead"><div>'
        '<div class="eyebrow"><i></i>Sessions</div>'
        "<h1>Sessions</h1><p>One row per participant. &ldquo;Ease&rdquo; is the "
        "participant's own score and is a feeling, not a measurement; treat it as a "
        "hint, not a metric.</p></div></div>")
    add('<div class="panel"><div class="scroll"><table><thead><tr>'
        "<th>Persona</th><th>Task</th><th>Outcome</th><th>Diff.</th><th>Ease</th>"
        "<th>Blockers</th><th>Friction</th><th>One thing to fix</th><th></th></tr></thead><tbody>")
    for s in sessions:
        result = s["result"]
        report = result.report
        counts = severity_counts(report)
        logdocs.append((s["log"], f"{s['name']} · {s['task']}", render_session_html(result, esc)))
        blockers = counts["blocker"]
        block_cell = f'<span class="bnum">{blockers}</span>' if blockers else '<span class="zero">0</span>'
        fix = report.get("one_thing_to_fix", "")
        if not result.ok and not fix:
            fix = f'<span style="color:var(--blocker)">Run problem: {esc(result.error or "unknown error")}</span>'
        else:
            fix = f'<span title="{esc(fix)}">{esc(fix)}</span>' if fix else '<span class="zero">-</span>'
        add(
            f'<tr><td><div class="who"><span class="ava">{s["icon"]}</span>'
            f'<span><span class="nm">{esc(s["name"])}</span><br>'
            f'<span class="dev">{esc(s["device"])} &middot; {_duration(s["duration"])}</span></span></div></td>'
            f'<td class="task">{esc(s["task"])}</td>'
            f'<td>{outcome_badge(s["outcome"])}</td>'
            f'<td class="num">{esc(_fmt(report.get("difficulty")))}</td>'
            f"<td>{_meter(s['ease'])}</td>"
            f'<td class="num">{block_cell}</td>'
            f'<td>{spark(s["steps"])}</td>'
            f'<td class="fixcell">{fix}</td>'
            f'<td><div class="acts">'
            + (f'<a class="abtn pri" href="#replay/{s["i"]}/0" data-replay="{s["i"]}:0">{ICON_PLAY}replay</a>' if s["steps"] else "")
            + f'<button class="abtn" type="button" data-log="{s["log"]}">log</button></div></td></tr>'
        )
    add("</tbody></table></div></div></section>")

    # ---- Replay -------------------------------------------------------------
    add('<section class="view" id="replay"><div class="vhead"><div>'
        '<div class="eyebrow"><i></i>Replay</div>'
        "<h1>Watch the session</h1><p>Every step the participant took, with the screenshot they "
        "saw and what they were thinking at that moment. Play it through or scrub with the arrow keys.</p></div></div>")
    if with_steps:
        add('<div class="rp-tabs">')
        for s in sessions:
            if not s["steps"]:
                continue
            add(f'<button class="rp-tab" type="button" data-s="{s["i"]}">'
                f'<span class="ava">{s["icon"]}</span>{esc(s["first"])}'
                f'<span class="st {esc(s["outcome"])}" title="{esc(s["outcome"])}"></span>'
                f'<span class="num" style="color:var(--faint);font-size:.7rem">{len(s["steps"])}</span></button>')
        add("</div>")
        add('<div id="replay-app"><div class="rp">'
            '<div class="rp-stage"><div class="rp-chrome"><i></i><i></i><i></i><span class="url"></span><span class="dev"></span></div>'
            '<div class="rp-shot"></div>'
            '<div class="rp-cap"><span class="act"></span><span class="fric"></span></div></div>'
            '<div class="rp-side"></div></div>'
            '<div class="rp-bar"><div class="rp-ctl">'
            f'<button class="ibtn first-btn" type="button" title="First step (Home)">{ICON_FIRST}</button>'
            f'<button class="ibtn prev-btn" type="button" title="Previous (←)">{ICON_LEFT}</button>'
            f'<button class="ibtn pri play-btn" type="button" aria-label="Play" title="Play / pause (space)">{ICON_PLAY}{ICON_PAUSE}</button>'
            f'<button class="ibtn next-btn" type="button" title="Next (→)">{ICON_RIGHT}</button>'
            f'<button class="ibtn last-btn" type="button" title="Last step (End)">{ICON_LAST}</button>'
            '<span class="pos"></span>'
            '<span class="hint"><span><kbd>←</kbd><kbd>→</kbd> step</span><span><kbd>space</kbd> play</span>'
            f'<a class="abtn open-shot" href="#" target="_blank" rel="noopener">{ICON_OUT}open image</a>'
            '<button class="abtn" type="button" data-log="log-0">full log</button></span></div>'
            '<div class="rp-tl"></div><div class="rp-axis"></div></div></div>')
        add('<noscript><div class="rp-none">The replay needs JavaScript. The session logs below have every step and screenshot.</div></noscript>')
    else:
        add('<div class="rp-none">No session in this study recorded steps, so there is nothing to replay yet.</div>')
    add("</section>")

    # ---- Issues -------------------------------------------------------------
    add('<section class="view" id="issues"><div class="vhead"><div>'
        '<div class="eyebrow"><i></i>Issues</div>'
        "<h1>What to fix</h1><p>Duplicate reports of one problem are merged into a single "
        "issue. &ldquo;Hit by&rdquo; counts distinct participants; &ldquo;measured&rdquo; "
        "means it was checked in the page rather than felt. Hover an issue to copy it as a ticket.</p></div></div>")
    if groups:
        add('<div class="fbar">')
        add('<div class="grp">' + "".join(
            f'<button class="chipb" type="button" data-filter="band" data-value="{esc(b)}">{lbl}</button>'
            for b, lbl in ((BAND_FIX_FIRST, "Fix first"), (BAND_NEXT, "Next"), (BAND_BACKLOG, "Backlog"))) + "</div>")
        add('<div class="grp">' + "".join(
            f'<button class="chipb {s}" type="button" data-filter="sev" data-value="{s}"><i></i>{s}</button>'
            for s in SEVERITIES) + "</div>")
        add('<div class="grp">' + "".join(
            f'<button class="chipb {g}" type="button" data-filter="grade" data-value="{g}" title="{esc(desc)}"><i></i>{g}</button>'
            for g, desc in ((MEASURED, "checked in the page"), (OBSERVED, "quoted from the screen"),
                            (IMPRESSION, "no evidence recorded"))) + "</div>")
        add('<div class="grp">' + "".join(
            f'<button class="chipb" type="button" data-filter="persona" data-value="{esc(p.id)}" title="{esc(p.name)}">'
            f'<span class="ava">{persona_icon(p)}</span>{esc(_first_name(p.name))}</button>'
            for p in personas_cols) + "</div>")
        add('<select id="sort" title="Sort within each band"><option value="impact">Sort: impact</option>'
            '<option value="reach">Sort: reach</option><option value="severity">Sort: severity</option></select>')
        add(f'<span class="tail"><button class="clear" type="button" style="display:none">clear filters</button>'
            f'<span class="count"><b>{len(groups)}</b> of {len(groups)}</span></span></div>')
        for band, label, desc in ((BAND_FIX_FIRST, "Fix first", "blockers, and anything several people hit and agreed was bad"),
                                  (BAND_NEXT, "Next", "real damage, narrower reach or lighter severity"),
                                  (BAND_BACKLOG, "Backlog", "polish and one-off annoyances")):
            band_groups = [g for g in groups if g["band"] == band]
            if not band_groups:
                continue
            add(f'<div class="band">{label} <span class="count">{len(band_groups)}</span><span class="desc">{desc}</span></div>')
            for group in band_groups:
                add(issue_card(group))
    else:
        add('<div class="empty">No issues were merged from these sessions.</div>')
    add("</section>")

    # ---- Gallery ------------------------------------------------------------
    if with_shots:
        add('<section class="view" id="gallery"><div class="vhead"><div>'
            '<div class="eyebrow"><i></i>Gallery</div>'
            "<h1>Gallery</h1><p>Every participant screenshots each meaningful step, wired to "
            "the moment that produced it. Click a frame to open it full size.</p></div></div>")
        for s in with_shots:
            shots = [(k, st) for k, st in enumerate(s["steps"]) if st["shot"]]
            add(f'<div class="gal"><h4><span class="ava">{s["icon"]}</span>{esc(s["name"])}'
                f'<span class="n">{len(shots)} frames</span>'
                f'<a class="abtn" href="#replay/{s["i"]}/0" data-replay="{s["i"]}:0">{ICON_PLAY}replay</a></h4><div class="strip">')
            for k, st in shots:
                src = f'{s["dir"]}/{st["shot"]}'
                caption = st["action"] or st["what"] or st["intent"] or st["shot"]
                fr = st["friction"]
                bars = "".join(f'<i class="{"on" + str(fr) if j <= fr else ""}"></i>' for j in (1, 2, 3))
                add(f'<figure><button type="button" data-shot="{s["i"]}:{k}">'
                    f'<img src="{esc(src)}" alt="{esc(caption)}" loading="lazy"></button>'
                    f'<figcaption><span class="n">{esc(_fmt(st["n"]))}</span><span>{esc(caption)}</span>'
                    f'<span class="fr" title="friction {fr}/3">{bars}</span></figcaption></figure>')
            add("</div></div>")
        add("</section>")

    # ---- Voices -------------------------------------------------------------
    if quotes or delights or impressions:
        add('<section class="view" id="voices"><div class="vhead"><div>'
            '<div class="eyebrow"><i></i>Voices</div>'
            "<h1>Voices</h1><p>In-character summaries, emotional arcs and the things that genuinely worked. "
            "Useful colour, not evidence.</p></div></div>")
        if quotes:
            add('<div class="qgrid">')
            for s in quotes:
                rep = s["result"].report
                add(f'<div class="quote"><p>{esc(rep["in_character_summary"])}</p>')
                if rep.get("emotional_arc"):
                    add(f'<div class="arc"><b>Emotional arc</b>{esc(rep["emotional_arc"])}</div>')
                add(f'<div class="cite"><span class="ava">{s["icon"]}</span>{esc(s["name"])}{outcome_badge(s["outcome"])}</div></div>')
            add("</div>")
        if impressions:
            add(f'<div class="band" style="margin-top:22px">First impressions <span class="count">{len(impressions)}</span>'
                '<span class="desc">the first fifteen seconds, in their words</span></div><div class="qgrid">')
            for s in impressions:
                add(f'<div class="quote"><p>{esc(s["result"].report["first_impression"])}</p>'
                    f'<div class="cite"><span class="ava">{s["icon"]}</span>{esc(s["name"])}</div></div>')
            add("</div>")
        if delights:
            add('<div class="band" style="margin-top:22px">What worked '
                f'<span class="count">{len(delights)}</span></div><ul class="worked">')
            for who, item in delights:
                add(f'<li>{esc(item)} <span class="by">({esc(_first_name(who))})</span></li>')
            add("</ul>")
        add("</section>")

    add('<div class="foot">These are simulated participants driven by a coding agent, not real '
        "users. Mechanical observations, like a control that does not respond, an unlabelled input "
        "or a console error, are reliable and worth acting on. Statements about how someone "
        "feels are hypotheses to check with real people, not measurements.</div>")
    add("</div></main></div>")

    # ---- hidden documents, overlays, data -----------------------------------
    for log_id, title, doc in logdocs:
        add(f'<div class="logsrc" id="{log_id}" data-title="{esc(title)}" hidden>{doc}</div>')
    add('<div class="modal" id="logmodal" role="dialog" aria-modal="true" aria-hidden="true">'
        '<div class="modal-card"><div class="modal-head"><span class="t"></span>'
        f'<button class="modal-close" type="button" aria-label="Close">{ICON_X}</button></div>'
        '<div class="modal-body logdoc"></div></div></div>')
    add('<div class="modal help" id="help" role="dialog" aria-modal="true" aria-hidden="true">'
        '<div class="modal-card"><div class="modal-head"><span class="t">Keyboard</span>'
        f'<button class="modal-close" type="button" aria-label="Close">{ICON_X}</button></div>'
        '<div class="modal-body"><table><tbody>'
        + "".join(f'<tr><td><kbd>{k}</kbd></td><td>{esc(label)}</td></tr>' for k, (vid, label, _, _) in enumerate(nav, start=1))
        + '<tr><td><kbd>/</kbd></td><td>Search issues</td></tr>'
        '<tr><td><kbd>←</kbd> <kbd>→</kbd></td><td>Previous / next step in the replay or lightbox</td></tr>'
        '<tr><td><kbd>space</kbd></td><td>Play / pause the replay</td></tr>'
        '<tr><td><kbd>Home</kbd> <kbd>End</kbd></td><td>First / last step</td></tr>'
        '<tr><td><kbd>t</kbd></td><td>Toggle light / dark</td></tr>'
        '<tr><td><kbd>[</kbd></td><td>Collapse the sidebar</td></tr>'
        '<tr><td><kbd>Esc</kbd></td><td>Close anything</td></tr>'
        '<tr><td><kbd>?</kbd></td><td>This list</td></tr>'
        '</tbody></table></div></div></div>')
    add('<div class="lb" id="lb" role="dialog" aria-modal="true" aria-hidden="true">'
        '<div class="lb-head"><span class="t"></span><span class="pos"></span>'
        f'<a class="abtn open-rp" href="#replay" data-replay="0:0" style="color:#fff;border-color:rgba(255,255,255,.25)">{ICON_PLAY}open in replay</a>'
        f'<button class="ibtn lb-close" type="button" aria-label="Close">{ICON_X}</button></div>'
        '<div class="lb-body"></div><div class="lb-foot"></div></div>')
    add('<div class="tip" id="tip" role="tooltip"></div><div class="toast" id="toast" role="status"></div>')
    add(f'<template id="ic-left">{ICON_LEFT}</template><template id="ic-right">{ICON_RIGHT}</template>')

    payload = {"sessions": [{k: v for k, v in s.items() if k != "result"} for s in sessions]}
    blob = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    add(f'<script type="application/json" id="uxp-data">{blob}</script>')
    add("<script>" + DASHBOARD_JS + "</script>")
    add("</body></html>")
    return "\n".join(parts)
