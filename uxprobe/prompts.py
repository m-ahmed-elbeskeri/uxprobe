"""Prompt construction: turns a RunSpec into the instruction text sent to the CLI agent."""

from __future__ import annotations

from .models import RunSpec, _bullets

# --------------------------------------------------------------------------
# browser guidance
# --------------------------------------------------------------------------

_BROWSER_HINTS = {
    "auto": (
        "Use whatever browser automation you have available. Check your tool list first. "
        "In rough order of preference:\n"
        "  1. Claude-in-Chrome MCP tools (mcp__claude-in-chrome__*) - navigate, computer, "
        "read_page, get_page_text, find, form_input, read_console_messages.\n"
        "  2. A Playwright / Puppeteer MCP server if one is connected.\n"
        "  3. Otherwise write a short Playwright Python or Node script in a scratch "
        "directory and run it, taking a screenshot after every interaction and printing "
        "the visible text so you can decide the next move.\n"
        "If you genuinely have no way to open a browser, say so in the JSON report with "
        'outcome "failed" and an explanation - do not invent an experience.'
    ),
    "chrome-mcp": (
        "Use the Claude-in-Chrome MCP tools. Call mcp__claude-in-chrome__tabs_context_mcp "
        "first, then open a NEW tab with tabs_create_mcp rather than reusing the user's "
        "tabs. Drive the page with navigate / computer / read_page / get_page_text / find "
        "/ form_input, and read_console_messages when something looks broken. "
        "Never trigger alert(), confirm() or prompt() dialogs - they freeze the session."
    ),
    "playwright-mcp": (
        "Use the connected Playwright MCP server. Take a snapshot or screenshot after "
        "every interaction so your reactions are based on what is actually on screen."
    ),
    "playwright-script": (
        "Write a Playwright script (Python or Node) in a scratch directory and run it "
        "step by step. After each interaction, screenshot to a file and print the visible "
        "text and any console errors, then decide the next action from that output. Do not "
        "write the whole session as one script up front - you must react to what you see."
    ),
    "none": (
        "You have no browser. Do not pretend to have used one. Instead reason about the "
        "site only from information you are given, and mark every observation as "
        "unverified in the report."
    ),
}

# --------------------------------------------------------------------------
# the JSON contract (kept out of f-strings because of the braces)
# --------------------------------------------------------------------------

_SCHEMA = r"""
{
  "outcome": "completed | partial | failed | abandoned",
  "difficulty": 1,
  "confidence": 1,
  "ease_score": 0,
  "would_return": true,
  "would_recommend": false,
  "first_impression": "What you thought in the first ten seconds, in character.",
  "emotional_arc": "How your mood moved from start to finish and what moved it.",
  "steps": [
    {
      "n": 1,
      "intent": "What you were trying to do at this moment.",
      "action": "What you actually did - the concrete interaction.",
      "expected": "What you expected to happen before you did it.",
      "what_happened": "What actually happened on screen.",
      "thought": "Your inner monologue, first person, in character.",
      "feeling": "one or two words: confident | confused | annoyed | delighted | anxious | bored | lost | relieved",
      "friction": 0,
      "seconds": 5,
      "screenshot": "relative/path/if/you/took/one.png"
    }
  ],
  "friction_points": [
    {
      "severity": "blocker | major | minor | nitpick",
      "where": "Page or component, specific enough to find it.",
      "what": "The problem, stated plainly.",
      "why_it_hurts": "The user consequence, not the code cause.",
      "evidence": "What you observed that proves it - exact label, error text, timing, console message.",
      "suggested_fix": "One concrete change.",
      "heuristic": "Which usability heuristic it violates, if one applies."
    }
  ],
  "delights": ["Things that genuinely worked well."],
  "confusions": ["Moments you did not know what to do next."],
  "unmet_expectations": ["Where the interface did something other than what you expected."],
  "accessibility_notes": ["Contrast, focus order, labelling, target size, motion."],
  "technical_observations": ["Console errors, slow requests, layout shift, broken images."],
  "pages_visited": ["https://..."],
  "questions_for_the_team": ["Things you would ask the people who built this."],
  "one_thing_to_fix": "If they could only change one thing, this is it.",
  "in_character_summary": "Two to four sentences, first person, as the persona. How it felt.",
  "analyst_summary": "Two to four sentences, out of character, as a UX researcher. What this run evidences.",
  "tags": ["navigation", "forms", "pricing"]
}
"""

_SCALES = """SCALES - use them consistently:
  difficulty  1 = effortless, 3 = had to think, 5 = could not work it out
  confidence  1 = never sure anything worked, 5 = always knew where I stood
  ease_score  0-100, how easy the whole thing felt (100 = trivially easy)
  friction    per step: 0 = smooth, 1 = a small snag, 2 = had to stop and think,
              3 = stuck, backtracked, or got it wrong
SEVERITY:
  blocker  stopped the task, or would make a real user leave
  major    cost real time or caused a wrong action, task still possible
  minor    noticeable annoyance, easily recovered
  nitpick  polish only"""


def build_prompt(spec: RunSpec) -> str:
    persona = spec.persona
    task = spec.task
    browser_hint = _BROWSER_HINTS.get(spec.browser, _BROWSER_HINTS["auto"])

    shots = ""
    if spec.screenshots:
        shots = (
            "\nSCREENSHOTS: take one at each meaningful state change and save it into the "
            "run directory given below, named 01-<slug>.png, 02-<slug>.png and so on. "
            "Reference the filename in the matching step's \"screenshot\" field.\n"
        )

    parts = [
        "You are running a moderated usability test, and you are playing the participant.",
        "",
        "Stay in character while you use the site. Step out of character exactly once, at "
        "the very end, for the analyst_summary field. Everything else is that person's "
        "experience, not yours.",
        "",
        "=== THE PARTICIPANT ===",
        persona.prompt_block(),
        "",
        "=== WHAT THEY ARE TRYING TO DO ===",
        task.prompt_block(),
        "",
        "=== HOW TO DRIVE THE BROWSER ===",
        browser_hint,
        shots,
        "=== HOUSE RULES (non-negotiable) ===",
        _bullets(task.guardrails, indent=""),
        "",
        "=== HOW TO BEHAVE ===",
        _bullets(
            [
                "Think aloud continuously. Before each click, say what you expect. After it, "
                "say whether that is what you got.",
                "React as this person would, not as a helpful assistant. If the persona is "
                "impatient, be impatient. If they would not read the help text, do not read it.",
                "Do not use knowledge the persona would not have. No reading the DOM to find a "
                "hidden button, no guessing URLs, no dev tools - unless the persona is technical "
                "enough to do that, in which case say so.",
                "If you get stuck, try what a real person would try next: scroll, look for "
                "search, check the nav, use the back button. Record each of those as a step.",
                "Giving up is a valid outcome and often the most useful one. Do not grind to a "
                "success the persona would never have reached.",
                "Be specific. 'The button was confusing' is worthless; 'the primary button says "
                "Continue but the secondary says Next, so I could not tell which moved forward' "
                "is a finding.",
                "Do not soften. If it is bad, say it is bad. If it is good, say that too - a "
                "report with no delights is as suspect as one with no problems.",
                "Quote real on-screen text in evidence fields. Never invent UI you did not see.",
            ],
            indent="",
        ),
        "",
        _SCALES,
        "",
        "=== OUTPUT ===",
        "Work through the task first. Then, as the LAST thing in your final message, emit a "
        "single fenced JSON block - ```json ... ``` - matching this shape exactly. No prose "
        "after it. Keys with nothing to say get an empty list or an empty string; do not drop "
        "them. Every step you actually took must appear in \"steps\".",
        "",
        "```json",
        _SCHEMA.strip(),
        "```",
    ]
    return "\n".join(parts)


def build_repair_prompt(previous_output: str, limit: int = 40000, truncated: bool = False) -> str:
    """Second-chance prompt when a run produced no parseable JSON.

    When `truncated`, the session was killed mid-flight, so the transcript stops
    somewhere arbitrary. Salvaging a partial report from it is far more useful than
    throwing away twenty minutes of real browsing.
    """
    tail = previous_output[-limit:]
    if truncated:
        opening = (
            "A usability-test session was cut short by a timeout before it could write its "
            "report. The transcript below is everything that happened up to the moment it "
            "was killed, it stops mid-flow, and that is expected.\n\n"
            "Do NOT redo the test and do NOT open a browser. Salvage a report from what is "
            "there.\n\n"
            "Rules for a salvaged report:\n"
            "  - Set \"outcome\" to what was actually true at the cut-off. If the task was "
            "not finished, that is \"abandoned\", not \"completed\".\n"
            "  - Include every step that appears in the transcript, and stop there.\n"
            "  - Only record findings the transcript actually evidences. Do not extrapolate "
            "what would probably have happened next.\n"
            "  - Add \"session cut short by timeout\" as the first item in "
            "\"technical_observations\".\n\n"
        )
    else:
        opening = (
            "Your previous usability-test run did not end with a parseable JSON report.\n\n"
            "Below is the tail of that run. Do NOT redo the test and do NOT open a browser "
            "again. Read what happened and convert it into the report.\n\n"
        )
    return (
        opening
        + "Reply with nothing except one fenced ```json block matching the schema you were "
        "given, filled in from the transcript below. If a field was never observed, use an "
        "empty string or empty list rather than inventing something.\n\n"
        "=== TRANSCRIPT ===\n"
        f"{tail}\n"
        "=== END TRANSCRIPT ===\n"
    )


def build_synthesis_prompt(reports_json: str, context: str = "") -> str:
    """Cross-run synthesis, used by `uxprobe synth`."""
    return (
        "You are the lead researcher writing up a usability study. Below are the JSON "
        "reports from every session in the study - several personas, several tasks.\n\n"
        f"{('STUDY CONTEXT: ' + context + chr(10) + chr(10)) if context else ''}"
        "Write a findings memo in Markdown with these sections:\n"
        "  1. Headline - the three sentences a product lead needs.\n"
        "  2. Severity-ranked issues - merge the same problem reported by different "
        "personas into one entry, note who hit it and who did not, and say whether it is "
        "universal or persona-specific. Cite evidence quotes.\n"
        "  3. Task outcomes - a table of persona x task with outcome and difficulty.\n"
        "  4. Where personas diverged - places one persona sailed through and another "
        "stalled, and what that implies about who this interface is built for.\n"
        "  5. What worked - do not skip this.\n"
        "  6. Recommended fixes in priority order, each with the expected effect.\n"
        "  7. Caveats - these are simulated participants; say plainly which findings are "
        "solid mechanical observations and which are inferences about how people feel.\n\n"
        "Do not average the scores into a single number and present it as a metric. "
        "Small n, simulated participants.\n\n"
        "=== SESSION REPORTS (JSON) ===\n"
        f"{reports_json}\n"
    )
