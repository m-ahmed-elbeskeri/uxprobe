"""Turning raw session findings into something you can act on.

Three questions decide whether a finding gets a ticket:

  1. Is it real?        -> evidence_grade(): did the participant measure it, quote it,
                           or just feel it?
  2. Who does it hit?   -> merge_findings(): the same problem reported by three personas
                           is a different proposition from one persona's annoyance.
  3. What does it cost? -> impact(): severity weighted by reach, confidence, and whether
                           anyone actually failed the task because of it.

The reporters read this module; nothing here touches disk or the network.
"""

from __future__ import annotations

import re
from typing import Any, Iterable

from .models import RunResult, SEVERITIES

# --------------------------------------------------------------------------
# 1. is it real?
# --------------------------------------------------------------------------

MEASURED = "measured"
OBSERVED = "observed"
IMPRESSION = "impression"

GRADE_ORDER = (MEASURED, OBSERVED, IMPRESSION)

GRADE_BLURB = {
    MEASURED: "Checked in the page, markup, computed style, timing or a key press with a "
              "recorded result. Reproduce it and you will see the same thing.",
    OBSERVED: "Quotes what was on screen but carries no measurement. Almost certainly real, "
              "worth one minute of confirming.",
    IMPRESSION: "No supporting evidence was recorded. Treat as a question to ask a real "
                "user, not as a defect report.",
}

# things only a machine check produces
_MEASURED_PATTERNS = (
    r"<[a-z]+[\s>]",                     # <p class=...>, <a href
    r"\baria-[a-z]+\b",                  # aria-label, aria-modal
    r"\brole\s*=",                       # role="button"
    r"\btabindex\b",
    r"\b(computed|opacity|pointer-events|overflow|z-index|scrollHeight|clientHeight)\b",
    r"\b\d+\s*px\b",
    r"\b\d+\s*(ms|s)\b",
    r"\b\d+\s*/\s*\d+\b",                # 0/40
    r"\b(rect|bounding|viewport)\b",
    r"\b(console|Error|error:|404|4\d\d|5\d\d)\b",
    r"\bdocument\.(activeElement|body)\b",
    r"\b(pressed|returned|resolves to|computes to|reported|logged|queried)\b",
    r"\b\d+\s*(tab|clicks?|presses|stops|tabs)\b",
    r"\bnull\b|\bundefined\b",
)
_MEASURED_RE = re.compile("|".join(_MEASURED_PATTERNS), re.IGNORECASE)
_QUOTE_RE = re.compile(r"['\"‘’“”][^'\"‘’“”]{3,}"
                       r"['\"‘’“”]")


def evidence_grade(finding: dict[str, Any]) -> str:
    """How much weight this finding can carry on its own."""
    evidence = " ".join(
        str(finding.get(key, "")) for key in ("evidence", "what", "where")
    ).strip()
    if not str(finding.get("evidence", "")).strip():
        # no evidence field at all: a quoted UI string in `what` still beats nothing
        return OBSERVED if _QUOTE_RE.search(evidence) else IMPRESSION
    if _MEASURED_RE.search(evidence):
        return MEASURED
    if _QUOTE_RE.search(evidence) or any(ch.isdigit() for ch in evidence):
        return OBSERVED
    return IMPRESSION


# --------------------------------------------------------------------------
# 2. who does it hit?
# --------------------------------------------------------------------------

_STOPWORDS = {
    "the", "a", "an", "is", "are", "to", "of", "and", "on", "in", "it", "that", "this",
    "for", "with", "no", "not", "you", "your", "was", "were", "at", "as", "be", "by",
    "but", "or", "if", "so", "then", "than", "there", "their", "them", "they", "when",
    "which", "what", "who", "from", "into", "only", "just", "also", "any", "all", "can",
    "does", "do", "did", "has", "have", "had", "its", "it's", "one", "two", "get", "got",
    "page", "site", "user", "users", "click", "clicked", "clicking",
}


def _stem(word: str) -> str:
    for suffix in ("ingly", "edly", "ing", "ies", "ied", "es", "ed", "s"):
        if len(word) > len(suffix) + 2 and word.endswith(suffix):
            return word[: -len(suffix)]
    return word


def _words(text: str) -> set[str]:
    text = str(text or "").lower().replace(",", "")  # 1,730 and 1730 are the same number
    return {_stem(w) for w in re.findall(r"[a-z]{3,}|\d{2,}", text) if w not in _STOPWORDS}


def _tokens(finding: dict[str, Any]) -> set[str]:
    return _words(f"{finding.get('what', '')} {finding.get('where', '')}")


def _what_tokens(finding: dict[str, Any]) -> set[str]:
    """Tokens from the defect description alone.

    Location words are treacherous: two unrelated bugs in one export dialog share
    'deck', 'dialog', 'export' and 'tab' and will merge on location alone. Requiring
    agreement in the *what* is a structural check that holds however few findings the
    study produced, corpus-relative rarity degenerates when there are only two.
    """
    return _words(finding.get("what", ""))


def _overlap(a: set[str], b: set[str]) -> float:
    """Overlap coefficient, not Jaccard.

    Jaccard divides by the union, so a terse finding and a verbose one describing the
    same defect score low purely because one of them said more. That is exactly the
    case that matters here, and it is why the first version of this failed to merge
    obvious duplicates.
    """
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))


def _idf(findings: list[dict[str, Any]]) -> dict[str, float]:
    """Rarity weight per token, over this study's own findings.

    Plain overlap cannot tell "same defect" from "same screen": two unrelated problems
    in one export dialog share deck / dialog / export / tab and merge wrongly, while a
    genuine duplicate described from two angles shares only a couple of rare words.
    Weighting by rarity puts the signal where it belongs, on 'onboarding' and
    'placeholder', not on 'deck'.
    """
    import math

    total = max(1, len(findings))
    df: dict[str, int] = {}
    for finding in findings:
        for token in _tokens(finding):
            df[token] = df.get(token, 0) + 1
    return {t: math.log(1 + total / n) for t, n in df.items()}


def _weighted_overlap(a: set[str], b: set[str], idf: dict[str, float]) -> float:
    shared = a & b
    if not shared:
        return 0.0
    weight = lambda s: sum(idf.get(t, 1.0) for t in s)  # noqa: E731
    denom = min(weight(a), weight(b))
    return weight(shared) / denom if denom else 0.0


MERGE_THRESHOLD = 0.42
MIN_SHARED_TOKENS = 2
# shared words in the defect description itself, independent of study size
MIN_SHARED_WHAT = 2
# a token seen in more than this share of the study's findings is scenery, not signal
COMMON_TOKEN_SHARE = 0.35

_SEV_RANK = {s: i for i, s in enumerate(SEVERITIES)}


def _flatten(results: Iterable[RunResult]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for result in results:
        report = result.report or {}
        outcome = report.get("outcome", "unknown")
        for finding in report.get("friction_points") or []:
            rows.append(
                {
                    **finding,
                    "persona": result.spec.persona.name,
                    "persona_id": result.spec.persona.id,
                    "device": result.spec.persona.device,
                    "task": result.spec.task.title,
                    "run_id": result.spec.run_id,
                    "outcome": outcome,
                    "truncated": result.truncated,
                }
            )
    return rows


def merge_findings(results: Iterable[RunResult]) -> list[dict[str, Any]]:
    """Collapse the same problem reported by different participants into one issue.

    Severity is deliberately *not* part of the match. Two people routinely rate the
    same defect differently, one calls the consent wall major, another minor, and
    splitting on that hides the very agreement we are looking for. The group takes the
    worst severity anyone gave it and records the disagreement.
    """
    findings = _flatten(results)
    idf = _idf(findings)
    df_cap = max(2, int(COMMON_TOKEN_SHARE * max(1, len(findings))))
    counts: dict[str, int] = {}
    for finding in findings:
        for token in _tokens(finding):
            counts[token] = counts.get(token, 0) + 1
    distinctive = {t for t, n in counts.items() if n <= df_cap}

    groups: list[dict[str, Any]] = []

    for finding in findings:
        tokens = _tokens(finding)
        what = _what_tokens(finding)
        target = None
        best = 0.0
        for group in groups:
            # 1. structural gate: the defect descriptions must actually agree
            if len(what & group["_what"]) < MIN_SHARED_WHAT:
                continue
            # 2. corpus gate: shared words must be rare enough to mean something
            if len(tokens & group["_tokens"] & distinctive) < MIN_SHARED_TOKENS:
                continue
            score = _weighted_overlap(tokens, group["_tokens"], idf)
            if score >= MERGE_THRESHOLD and score > best:
                target, best = group, score

        grade = evidence_grade(finding)
        if target is None:
            groups.append(
                {
                    "what": finding.get("what", ""),
                    "where": finding.get("where", ""),
                    "why_it_hurts": finding.get("why_it_hurts", ""),
                    "severity": finding.get("severity", "minor"),
                    "severities": {finding.get("severity", "minor")},
                    "grades": {grade},
                    "evidence": [e for e in [finding.get("evidence")] if e],
                    "fixes": [f for f in [finding.get("suggested_fix")] if f],
                    "heuristics": {h for h in [finding.get("heuristic")] if h},
                    "personas": [finding["persona"]],
                    "tasks": [finding["task"]],
                    "outcomes": [finding["outcome"]],
                    "by_persona": {finding["persona"]: finding.get("severity", "minor")},
                    "reports": 1,
                    "_tokens": tokens,
                    "_what": what,
                }
            )
            continue

        target["reports"] += 1
        target["severities"].add(finding.get("severity", "minor"))
        target["grades"].add(grade)
        # the worst severity anyone assigned wins
        if _SEV_RANK.get(finding.get("severity", "minor"), 9) < _SEV_RANK.get(target["severity"], 9):
            target["severity"] = finding.get("severity", "minor")
            target["what"] = finding.get("what", "") or target["what"]
        if finding.get("persona") not in target["personas"]:
            target["personas"].append(finding["persona"])
        if finding.get("task") not in target["tasks"]:
            target["tasks"].append(finding["task"])
        target["outcomes"].append(finding["outcome"])
        current = target["by_persona"].get(finding["persona"])
        incoming = finding.get("severity", "minor")
        if current is None or _SEV_RANK.get(incoming, 9) < _SEV_RANK.get(current, 9):
            target["by_persona"][finding["persona"]] = incoming
        for key, dest in (("evidence", "evidence"), ("suggested_fix", "fixes")):
            value = finding.get(key)
            if value and value not in target[dest]:
                target[dest].append(value)
        if finding.get("heuristic"):
            target["heuristics"].add(finding["heuristic"])
        if not target["why_it_hurts"]:
            target["why_it_hurts"] = finding.get("why_it_hurts", "")
        target["_tokens"] = target["_tokens"] | tokens
        target["_what"] = target["_what"] | what

    for group in groups:
        group["_match_tokens"] = group.pop("_tokens", set())
        group.pop("_what", None)
        group["grade"] = next(g for g in GRADE_ORDER if g in group["grades"])
        group["disputed"] = len(group["severities"]) > 1
        group["severities"] = sorted(group["severities"], key=lambda s: _SEV_RANK.get(s, 9))
        group["grades"] = sorted(group["grades"], key=GRADE_ORDER.index)
    return groups


# --------------------------------------------------------------------------
# 3. what does it cost?
# --------------------------------------------------------------------------

_SEV_WEIGHT = {"blocker": 100.0, "major": 40.0, "minor": 12.0, "nitpick": 3.0}
_GRADE_WEIGHT = {MEASURED: 1.0, OBSERVED: 0.85, IMPRESSION: 0.6}
_BAD_OUTCOMES = {"failed", "abandoned", "partial"}


def corroborators(group: dict[str, Any]) -> int:
    """Participants who rated this at, or close to, the group's worst severity.

    Reach must not be inflated by someone who shrugged at it. The onboarding tour was
    a blocker for the screen-reader user and a one-click annoyance for everyone else;
    counting all three as "reach" would rank it above a defect that stops the site's
    core function outright.
    """
    worst = _SEV_RANK.get(group["severity"], 9)
    return max(1, sum(1 for sev in group["by_persona"].values()
                      if _SEV_RANK.get(sev, 9) - worst <= 1))


def impact(group: dict[str, Any], total_personas: int) -> float:
    """Severity, amplified by corroboration, evidence quality and task damage."""
    base = _SEV_WEIGHT.get(group["severity"], 12.0)
    agree = corroborators(group)
    reach = 1.0 + 0.6 * (agree - 1)
    if total_personas > 1 and agree == total_personas:
        reach *= 1.25  # everyone we tested hit this, and agreed how bad it was
    confidence = _GRADE_WEIGHT.get(group["grade"], 0.8)
    blocked = 1.3 if any(o in _BAD_OUTCOMES for o in group["outcomes"]) else 1.0
    # participants were each asked for the single thing they would fix; that is a
    # priority signal straight from the person who hit the problem
    named = 1.0 + 0.15 * len(group.get("named_by", []))
    return base * reach * confidence * blocked * named


BAND_FIX_FIRST = "fix first"
BAND_NEXT = "next"
BAND_BACKLOG = "backlog"


def prioritise(results: Iterable[RunResult]) -> list[dict[str, Any]]:
    """Rank merged issues by impact and band them for a planning conversation."""
    results = [r for r in results if (r.report or {}).get("friction_points")]
    total_personas = len({r.spec.persona.id for r in results}) or 1
    groups = merge_findings(results)

    # each participant's own "if you fix one thing" answer, matched back to an issue
    wishes = [
        (r.spec.persona.name, _tokens({"what": (r.report or {}).get("one_thing_to_fix", "")}))
        for r in results
        if (r.report or {}).get("one_thing_to_fix")
    ]

    for group in groups:
        group["named_by"] = [
            who for who, wish in wishes
            if wish and _overlap(wish, group["_match_tokens"]) >= 0.5
        ]
        group["reach"] = len(group["personas"])
        group["agreeing"] = corroborators(group)
        group["total_personas"] = total_personas
        group["universal"] = total_personas > 1 and group["reach"] == total_personas
        group["impact"] = round(impact(group, total_personas), 1)
    groups.sort(key=lambda g: -g["impact"])
    for rank, group in enumerate(groups, start=1):
        group["rank"] = rank
        if group["severity"] == "blocker" or group["impact"] >= 90:
            group["band"] = BAND_FIX_FIRST
        elif group["impact"] >= 34:
            group["band"] = BAND_NEXT
        else:
            group["band"] = BAND_BACKLOG
    return groups


def study_stats(results: list[RunResult]) -> dict[str, Any]:
    """The handful of numbers a status update actually needs."""
    reported = [r for r in results if r.ok]
    groups = prioritise(results)
    outcomes: dict[str, int] = {}
    for result in reported:
        key = result.report.get("outcome", "unknown")
        outcomes[key] = outcomes.get(key, 0) + 1
    spend = sum(
        float(r.agent_meta.get("total_cost_usd") or 0)
        for r in results
        if isinstance(r.agent_meta.get("total_cost_usd"), (int, float))
    )
    return {
        "sessions": len(results),
        "reported": len(reported),
        "truncated": sum(1 for r in results if r.truncated),
        "failed": sum(1 for r in results if not r.ok),
        "personas": len({r.spec.persona.id for r in results}),
        "tasks": len({r.spec.task.id for r in results}),
        "outcomes": outcomes,
        "raw_findings": sum(len(r.report.get("friction_points") or []) for r in reported),
        "issues": len(groups),
        "fix_first": sum(1 for g in groups if g["band"] == BAND_FIX_FIRST),
        "universal": sum(1 for g in groups if g["universal"]),
        "measured": sum(1 for g in groups if g["grade"] == MEASURED),
        "impressions": sum(1 for g in groups if g["grade"] == IMPRESSION),
        "spend": round(spend, 2),
        "minutes": round(sum(r.duration_s for r in results) / 60.0),
    }


# --------------------------------------------------------------------------
# ticket-ready text
# --------------------------------------------------------------------------


def issue_ticket(group: dict[str, Any]) -> str:
    """One merged issue as a paste-into-the-tracker block."""
    lines = [f"### {group['what']}", ""]
    meta = [
        f"**Severity:** {group['severity']}",
        f"**Hit by:** {group['reach']} of {group['total_personas']} participants "
        f"({', '.join(group['personas'])})",
        f"**Evidence:** {group['grade']}",
        f"**Impact score:** {group['impact']}",
    ]
    if group.get("where"):
        meta.insert(1, f"**Where:** {group['where']}")
    if group.get("disputed"):
        meta.append(f"**Note:** rated differently by different participants "
                    f"({', '.join(group['severities'])})")
    lines += meta + [""]
    if group.get("why_it_hurts"):
        lines += [f"**Why it matters.** {group['why_it_hurts']}", ""]
    if group.get("evidence"):
        lines += ["**Observed:**", ""]
        lines += [f"- {e}" for e in group["evidence"][:4]] + [""]
    if group.get("fixes"):
        lines += ["**Suggested fix:**", ""]
        lines += [f"- {f}" for f in group["fixes"][:3]] + [""]
    if group.get("heuristics"):
        lines += [f"<sub>Heuristic: {', '.join(sorted(group['heuristics']))}</sub>", ""]
    return "\n".join(lines)
