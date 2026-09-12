"""Smoke tests for the fiddly bits: report extraction, normalisation, grouping, config."""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from uxprobe.agents import extract_report, make_custom_backend  # noqa: E402
from uxprobe.config import load_study  # noqa: E402
from uxprobe.models import Persona, RunResult, RunSpec, Task, normalize_report  # noqa: E402
from uxprobe.personas import get_persona  # noqa: E402
from uxprobe.prompts import build_prompt  # noqa: E402
from uxprobe.analysis import corroborators, merge_findings  # noqa: E402
from uxprobe.reporting import render_run_markdown  # noqa: E402


def _result(findings, persona="first-timer"):
    spec = RunSpec(persona=get_persona(persona), task=Task.from_dict({"title": "t", "goal": "g"}))
    return RunResult(spec=spec, run_dir="x", ok=True,
                     report=normalize_report({"outcome": "partial", "friction_points": findings}))


class TestExtraction(unittest.TestCase):
    def test_fenced_block(self):
        text = 'blah blah\n```json\n{"outcome": "completed", "steps": []}\n```\ntrailing'
        self.assertEqual(extract_report(text)["outcome"], "completed")

    def test_prefers_the_report_over_other_json(self):
        text = ('```json\n{"unrelated": 1}\n```\n'
                '```json\n{"outcome": "failed", "steps": [], "friction_points": []}\n```')
        self.assertEqual(extract_report(text)["outcome"], "failed")

    def test_unfenced_object(self):
        text = 'I am done.\n{"outcome": "abandoned", "steps": [], "analyst_summary": "x"}\n'
        self.assertEqual(extract_report(text)["outcome"], "abandoned")

    def test_braces_inside_strings_do_not_break_scanning(self):
        text = '{"outcome": "completed", "steps": [], "analyst_summary": "a } brace { here"}'
        self.assertEqual(extract_report(text)["analyst_summary"], "a } brace { here")

    def test_no_report(self):
        self.assertIsNone(extract_report("I looked at the site. It was fine."))


class TestNormalisation(unittest.TestCase):
    def test_coerces_legacy_and_loose_values(self):
        report = normalize_report(
            {
                "task_completed": True,
                "difficulty": "7",  # out of range
                "sus_score": 88.4,
                "friction_points": [{"severity": "CRITICAL", "issue": "broken"}],
                "delights": "one line\ntwo lines",
            }
        )
        self.assertEqual(report["outcome"], "completed")
        self.assertEqual(report["difficulty"], 5)
        self.assertEqual(report["ease_score"], 88)
        self.assertEqual(report["friction_points"][0]["severity"], "blocker")
        self.assertEqual(report["friction_points"][0]["what"], "broken")
        self.assertEqual(report["delights"], ["one line", "two lines"])

    def test_garbage_input_does_not_raise(self):
        for junk in (None, [], "text", {"steps": "not a list"}, {"friction_points": ["a string"]}):
            self.assertIsInstance(normalize_report(junk), dict)

    def test_findings_are_severity_sorted(self):
        report = normalize_report(
            {"friction_points": [{"severity": "nitpick", "what": "a"},
                                 {"severity": "blocker", "what": "b"}]}
        )
        self.assertEqual([f["what"] for f in report["friction_points"]], ["b", "a"])


class TestGrouping(unittest.TestCase):
    """Baseline merge behaviour; see TestMergeQuality for the real-world cases."""
    def test_same_issue_across_personas_merges(self):
        finding = {"severity": "blocker", "what": "The headline never says what the product does",
                   "where": "Homepage hero"}
        groups = merge_findings([_result([finding], "first-timer"),
                                 _result([finding], "power-user")])
        self.assertEqual(len(groups), 1)
        self.assertEqual(len(groups[0]["personas"]), 2)

    def test_different_issues_stay_apart(self):
        groups = merge_findings(
            [_result([{"severity": "blocker", "what": "Headline says nothing", "where": "hero"},
                      {"severity": "blocker", "what": "Checkout rejects valid postcodes",
                       "where": "payment"}])]
        )
        self.assertEqual(len(groups), 2)

    def test_severity_disagreement_merges_and_is_flagged(self):
        """Two people rating one defect differently is signal, not a reason to split it."""
        groups = merge_findings(
            [_result([{"severity": "blocker", "what": "Tour overlay traps keyboard focus",
                       "where": "onboarding"}], "screen-reader"),
             _result([{"severity": "minor", "what": "Tour overlay traps keyboard focus",
                       "where": "onboarding"}], "power-user")]
        )
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["severity"], "blocker")  # worst rating wins
        self.assertTrue(groups[0]["disputed"])
        # ...but the person who shrugged must not inflate the reach used for ranking
        self.assertEqual(corroborators(groups[0]), 1)


class TestPromptAndRender(unittest.TestCase):
    def test_prompt_contains_persona_task_and_guardrails(self):
        spec = RunSpec(
            persona=get_persona("screen-reader"),
            task=Task.from_dict({"title": "Log in", "goal": "Get into the account",
                                 "url": "https://example.com"}),
        )
        prompt = build_prompt(spec)
        self.assertIn("Screen reader user", prompt)
        self.assertIn("https://example.com", prompt)
        self.assertIn("Do not complete any purchase", prompt)
        self.assertIn("```json", prompt)

    def test_markdown_renders_with_a_sparse_report(self):
        result = _result([])
        result.report = normalize_report({"outcome": "failed"})
        markdown = render_run_markdown(result)
        self.assertIn("failed", markdown)

    def test_pipe_characters_do_not_break_the_step_table(self):
        result = _result([])
        result.report = normalize_report(
            {"steps": [{"n": 1, "action": "typed a|b", "what_happened": "line\nbreak"}]}
        )
        table_row = [ln for ln in render_run_markdown(result).splitlines() if "typed" in ln][0]
        self.assertIn(r"typed a\|b", table_row)  # escaped, so the column count survives
        self.assertNotIn("\n", table_row)
        self.assertEqual(len(re.findall(r"(?<!\\)\|", table_row)), 8)  # 7 columns


class TestConfig(unittest.TestCase):
    def test_study_json_with_extends_and_guardrails(self):
        study_doc = {
            "name": "s",
            "base_url": "https://example.com",
            "personas": ["first-timer", {"extends": "power-user", "id": "pu2", "patience": "high"}],
            "tasks": [{"title": "Do it", "goal": "Do the thing"}],
            "guardrails": ["Extra rule"],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "study.json")
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(study_doc, handle)
            study = load_study(path)
        self.assertEqual([p.id for p in study.personas], ["first-timer", "pu2"])
        self.assertEqual(study.personas[1].patience, "high")
        self.assertEqual(study.tasks[0].url, "https://example.com")
        self.assertIn("Extra rule", study.tasks[0].guardrails)
        self.assertTrue(any("purchase" in g for g in study.tasks[0].guardrails))
        self.assertEqual(len(study.expand()), 2)


class TestCustomBackend(unittest.TestCase):
    def test_prompt_as_argument(self):
        # build() resolves the exe on PATH, so assert on the template instead
        backend = make_custom_backend("mycli --flag {prompt}")
        self.assertEqual(backend.prompt_mode, "arg")
        self.assertEqual(backend.prompt_arg_template, ["--flag", "{prompt}"])

    def test_prompt_via_stdin(self):
        backend = make_custom_backend("mycli --stdin-mode")
        self.assertEqual(backend.prompt_mode, "stdin")
        self.assertEqual(backend.base_args, ["--stdin-mode"])


if __name__ == "__main__":
    unittest.main(verbosity=2)


# --------------------------------------------------------------------------
# decision layer
# --------------------------------------------------------------------------

from uxprobe.analysis import (  # noqa: E402
    IMPRESSION, MEASURED, OBSERVED, corroborators, evidence_grade, merge_findings,
    prioritise, study_stats,
)
from uxprobe.agents import _extract_ndjson  # noqa: E402
from uxprobe.prompts import build_repair_prompt  # noqa: E402


def _res(persona, findings, outcome="completed", one_thing=""):
    spec = RunSpec(persona=get_persona(persona),
                   task=Task.from_dict({"title": "Build a deck", "goal": "g"}))
    return RunResult(spec=spec, run_dir="x", ok=True, report=normalize_report(
        {"outcome": outcome, "friction_points": findings, "one_thing_to_fix": one_thing}))


class TestEvidenceGrade(unittest.TestCase):
    def test_dom_measurement_is_measured(self):
        self.assertEqual(evidence_grade({
            "what": "Tiles ignore Enter",
            "evidence": 'Card tiles are div role="button" tabindex="0"; pressed Enter, '
                        "counter stayed 0/40."}), MEASURED)

    def test_quoted_ui_text_is_observed(self):
        self.assertEqual(evidence_grade({
            "what": "Confusing label",
            "evidence": "The button simply said 'Continue' where I expected 'Next'."}), OBSERVED)

    def test_no_evidence_is_an_impression(self):
        self.assertEqual(evidence_grade({
            "what": "The whole flow felt clunky and unpleasant", "evidence": ""}), IMPRESSION)


class TestMergeQuality(unittest.TestCase):
    """The two real failures found by running this against a live site."""

    DANA = {"severity": "major", "where": "Deck builder, right-hand deck panel - the 'Add' and "
            "'Select' boxes under Legend and Champion on an empty deck",
            "what": "The empty-slot boxes are styled as buttons but do nothing when clicked, "
                    "and give no feedback explaining why."}
    RAVI = {"severity": "major", "where": "Deck builder, right-hand deck panel - empty-slot "
            "placeholders ('Select' under Champion, 'Add 3 Battlefields', 'Add 12 Runes')",
            "what": "Empty deck slots are filled with imperative, button-styled text that is "
                    "completely inert."}
    # same dialog, different defects, must NOT merge
    NAME_FIELD = {"severity": "minor", "where": "Export dialog - Registration tab, 'Deck Name' "
                  "field", "what": "The field ships with the literal value 'Deck' already in it."}
    CODE_BOX = {"severity": "minor", "where": "Export Deck dialog - Code tab",
                "what": "The textbox holding the deck code has no accessible name."}

    def test_same_defect_worded_differently_merges(self):
        groups = merge_findings([_res("first-timer", [self.DANA]),
                                 _res("power-user", [self.RAVI])])
        self.assertEqual(len(groups), 1, "differently-worded duplicates must merge")
        self.assertEqual(len(groups[0]["personas"]), 2)

    def test_same_screen_different_defects_stay_apart(self):
        groups = merge_findings([_res("first-timer", [self.NAME_FIELD]),
                                 _res("power-user", [self.CODE_BOX])])
        self.assertEqual(len(groups), 2, "shared location words must not merge two defects")

    def test_merging_ignores_severity_and_keeps_the_worst(self):
        mild = {**self.DANA, "severity": "minor"}
        groups = merge_findings([_res("first-timer", [mild]), _res("power-user", [self.RAVI])])
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["severity"], "major")
        self.assertTrue(groups[0]["disputed"])


class TestPrioritisation(unittest.TestCase):
    def test_a_shrug_does_not_inflate_reach(self):
        group = {"severity": "blocker", "by_persona": {"A": "blocker", "B": "minor"}}
        self.assertEqual(corroborators(group), 1)

    def test_agreement_counts(self):
        group = {"severity": "major", "by_persona": {"A": "major", "B": "blocker"}}
        self.assertEqual(corroborators(group), 2)

    def test_blockers_land_in_fix_first_and_rank_above_nitpicks(self):
        blocker = {"severity": "blocker", "what": "Keyboard cannot activate card tiles",
                   "where": "gallery", "evidence": 'div role="button" with no handler'}
        nit = {"severity": "nitpick", "what": "Chart label clipped at the top of the panel",
               "where": "stats", "evidence": "the 12 is cut in half"}
        groups = prioritise([_res("screen-reader", [blocker], outcome="partial"),
                             _res("first-timer", [nit])])
        self.assertEqual(groups[0]["band"], "fix first")
        self.assertIn("Keyboard", groups[0]["what"])
        self.assertGreater(groups[0]["impact"], groups[-1]["impact"])

    def test_stats_do_not_crash_on_a_failed_session(self):
        dead = RunResult(spec=RunSpec(persona=get_persona("first-timer"),
                                      task=Task.from_dict({"title": "t", "goal": "g"})),
                         run_dir="x", ok=False, report={}, truncated=True)
        stats = study_stats([dead])
        self.assertEqual(stats["failed"], 1)
        self.assertEqual(stats["truncated"], 1)
        self.assertEqual(stats["issues"], 0)


class TestStreamingSurvivesTruncation(unittest.TestCase):
    def test_assistant_text_is_recovered_without_a_result_envelope(self):
        """A killed session never emits the final envelope; the prose must still come out."""
        stream = "\n".join([
            json.dumps({"type": "system", "subtype": "init", "session_id": "abc"}),
            json.dumps({"type": "assistant", "message": {"content": [
                {"type": "text", "text": "Clicked Select. Nothing happened."}]}}),
            json.dumps({"type": "assistant", "message": {"content": [
                {"type": "tool_use", "name": "Bash", "input": {"command": "node step.cjs"}}]}}),
            json.dumps({"type": "assistant", "message": {"content": [
                {"type": "text", "text": "Still nothing. This control is dead."}]}}),
        ])
        text, _ = _extract_ndjson(stream)
        self.assertIn("Clicked Select", text)
        self.assertIn("This control is dead", text)

    def test_result_envelope_still_wins_when_present(self):
        stream = "\n".join([
            json.dumps({"type": "assistant", "message": {"content": [
                {"type": "text", "text": "working"}]}}),
            json.dumps({"type": "result", "result": "```json\n{\"outcome\":\"completed\"}\n```",
                        "total_cost_usd": 3.78, "num_turns": 64}),
        ])
        text, meta = _extract_ndjson(stream)
        self.assertIn("completed", text)
        self.assertEqual(meta["total_cost_usd"], 3.78)

    def test_salvage_prompt_tells_the_model_it_was_cut_short(self):
        prompt = build_repair_prompt("a" * 500, truncated=True)
        self.assertIn("cut short", prompt)
        self.assertIn("abandoned", prompt)
