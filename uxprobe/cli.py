"""Command line interface for uxprobe."""

from __future__ import annotations

import argparse
import glob
import json
import re
import os
import sys
import webbrowser

from . import __version__
from .agents import AgentError, available_backends, get_backend, run_agent
from .config import EXAMPLE_STUDY, ConfigError, Study, load_study
from .models import Persona, RunResult, RunSpec, Task, slugify
from .personas import BUILTIN_PERSONAS, list_personas
from .analysis import study_stats
from .prompts import build_synthesis_prompt
from .reporting import render_run_markdown
from .runner import execute_study, make_out_dir, say, write_study_reports

BROWSER_CHOICES = ["auto", "chrome-mcp", "playwright-mcp", "playwright-script", "none"]


# --------------------------------------------------------------------------
# shared arguments
# --------------------------------------------------------------------------


def _add_agent_args(parser: argparse.ArgumentParser) -> None:
    group = parser.add_argument_group("agent")
    group.add_argument("--agent", default=None,
                       help="which coding CLI drives the browser (default: claude). "
                            "Use 'custom' with --cmd for anything else.")
    group.add_argument("--cmd", default="",
                       help="command template for --agent custom, e.g. "
                            "\"mycli --headless {prompt}\". Omit {prompt} to pipe via stdin.")
    group.add_argument("--model", default=None, help="model id passed through to the CLI")
    group.add_argument("--yolo", action="store_true",
                       help="pass the CLI's skip-permissions flag (unattended runs)")
    group.add_argument("--extra-arg", dest="extra_args", action="append", default=[],
                       help="extra argument passed through to the CLI; repeatable. Use the "
                            "= form for anything starting with a dash, or argparse eats it: "
                            "--extra-arg=--allowed-tools --extra-arg=\"Bash,Write,Read\"")
    group.add_argument("--timeout", type=int, default=None,
                       help="seconds per session before the agent is killed (default 900)")


def _add_output_args(parser: argparse.ArgumentParser) -> None:
    group = parser.add_argument_group("output")
    group.add_argument("--out", default="runs", help="root directory for run artefacts")
    group.add_argument("--concurrency", type=int, default=1,
                       help="parallel sessions (keep at 1 when sharing one browser)")
    group.add_argument("--echo", action="store_true",
                       help="stream the agent's output to the console as it works")
    group.add_argument("--repair-attempts", type=int, default=1,
                       help="retries asking the agent to reformat a missing JSON report")
    group.add_argument("--dry-run", action="store_true",
                       help="write the prompts but do not invoke any agent")
    group.add_argument("--open", dest="open_report", action="store_true",
                       help="open the HTML report when finished")
    group.add_argument("--resume", metavar="RUN_DIR", default="",
                       help="reuse an existing run directory and only run the sessions that "
                            "have no usable report yet")
    group.add_argument("--max-cost", type=float, default=0.0, metavar="USD",
                       help="stop starting new sessions once this much has been spent")
    group.add_argument("--est-cost", type=float, default=0.0, metavar="USD",
                       help="your own per-session cost estimate for the pre-flight (default: "
                            "4.00 for browser-driving runs)")
    group.add_argument("-y", "--yes", action="store_true",
                       help="skip the cost confirmation prompt")


# --------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------


def cmd_run(args: argparse.Namespace) -> int:
    if not args.tasks:
        say("error: give at least one --task")
        return 2

    persona_ids = args.personas or ["first-timer"]
    if len(persona_ids) == 1 and persona_ids[0].lower() == "all":
        personas = list_personas()
    else:
        personas = []
        for name in persona_ids:
            persona = BUILTIN_PERSONAS.get(name.strip().lower())
            if persona is None:
                if os.path.exists(name):
                    from .config import load_data_file

                    data = load_data_file(name)
                    entries = data.get("personas", [data]) if isinstance(data, dict) else data
                    personas.extend(Persona.from_dict(e) for e in entries)
                    continue
                say(f"error: unknown persona '{name}'. Run `uxprobe personas` for the list.")
                return 2
            personas.append(persona)

    tasks = []
    for i, text in enumerate(args.tasks, start=1):
        title = text if len(text) <= 60 else text[:57] + "..."
        tasks.append(
            Task.from_dict(
                {
                    "id": f"{i:02d}-{slugify(title, 32)}",
                    "title": title,
                    "goal": text,
                    "url": args.url,
                    "max_steps": args.max_steps,
                    "success_criteria": args.success or [],
                }
            )
        )

    study = Study(
        name=args.name or (slugify(args.url or "adhoc", 32) if args.url else "adhoc"),
        base_url=args.url,
        personas=personas,
        tasks=tasks,
        agents=[args.agent or "claude"],
        model=args.model or "",
        repeat=args.repeat,
        browser=args.browser,
        timeout=args.timeout or 900,
        yolo=args.yolo,
        screenshots=not args.no_screenshots,
        extra_args=args.extra_args,
    )
    return _execute(study, args)


def cmd_study(args: argparse.Namespace) -> int:
    try:
        study = load_study(args.file)
    except ConfigError as exc:
        say(f"error: {exc}")
        return 2

    # command-line flags override what the file says
    if args.agent:
        study.agents = [args.agent]
    if args.model:
        study.model = args.model
    if args.timeout:
        study.timeout = args.timeout
    if args.browser:
        study.browser = args.browser
    if args.yolo:
        study.yolo = True
    if args.repeat:
        study.repeat = args.repeat
    if args.extra_args:
        study.extra_args = args.extra_args
    if args.only:
        wanted = {w.strip().lower() for w in args.only}
        study.personas = [p for p in study.personas if p.id.lower() in wanted] or study.personas
        study.tasks = [t for t in study.tasks if t.id.lower() in wanted] or study.tasks
    return _execute(study, args)


def _execute(study: Study, args: argparse.Namespace) -> int:
    specs: list[RunSpec] = study.expand()
    if not specs:
        say("error: nothing to run")
        return 2

    # fail before creating an output directory if a CLI is missing
    if not args.dry_run:
        for agent in study.agents:
            try:
                get_backend(agent, args.cmd).resolve_exe()
            except AgentError as exc:
                say(f"error: {exc}")
                return 2

    # --- pre-flight: say what this will cost before spending anything -------------
    per_session = args.est_cost or (0.60 if study.browser == "none" else 4.00)
    est_total = per_session * len(specs)
    est_minutes = (2 if study.browser == "none" else 20) * len(specs) / max(1, args.concurrency)
    if not args.dry_run:
        say(f"pre-flight: {len(specs)} session(s) × ~${per_session:.2f} "
            f"≈ \033[1m${est_total:.0f}\033[0m and ~{est_minutes:.0f} min wall clock "
            f"at concurrency {args.concurrency}")
        if est_total >= 25 and not args.yes:
            if not sys.stdin.isatty():
                say("refusing to start: estimate is over $25 and this is not an interactive "
                    "terminal. Re-run with --yes, or narrow the study with --only.")
                return 2
            try:
                answer = input("  continue? [y/N] ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                answer = ""
            if answer not in ("y", "yes"):
                say("cancelled")
                return 1

    if args.resume:
        out_dir = args.resume
        if not os.path.isdir(out_dir):
            say(f"error: --resume directory does not exist: {out_dir}")
            return 2
    else:
        out_dir = make_out_dir(args.out, study.name)
    say(f"uxprobe {__version__}")
    say(f"study    {study.name}"
        + (f", {study.description}" if study.description else ""))
    say(f"sessions {len(specs)}  ({len(study.personas)} persona(s) x {len(study.tasks)} task(s)"
        f"{f' x {study.repeat} repeats' if study.repeat > 1 else ''}"
        f"{f' x {len(study.agents)} agents' if len(study.agents) > 1 else ''})")
    say(f"agent    {', '.join(study.agents)}"
        + (f" · model {study.model}" if study.model else "")
        + f" · browser {study.browser}"
        + (" · YOLO permissions" if study.yolo else ""))
    say(f"output   {out_dir}")
    say("")

    results = execute_study(
        specs,
        out_dir,
        study.name,
        custom_cmd=args.cmd,
        concurrency=max(1, args.concurrency),
        echo=args.echo,
        repair_attempts=max(0, args.repair_attempts),
        dry_run=args.dry_run,
        resume=bool(args.resume),
        max_cost=args.max_cost,
    )

    say("")
    ok = sum(1 for r in results if r.ok)
    if args.dry_run:
        say(f"dry run: {len(results)} prompt(s) written under {out_dir}")
        say("  inspect any run's prompt.txt, then re-run without --dry-run")
        return 0
    stats = study_stats(results)
    say(f"done: {ok}/{len(results)} session(s) produced a report"
        + (f", {stats['truncated']} salvaged from a cut-short transcript"
           if stats["truncated"] else ""))
    if ok < len(results):
        say(f"  {len(results) - ok} session(s) had problems, rerun just those with "
            f"--resume {out_dir}")
    say(f"  {stats['fix_first']} issue(s) to fix first, {stats['issues']} in total "
        f"(from {stats['raw_findings']} raw findings) · spent ${stats['spend']:.2f}")
    say(f"  {os.path.join(out_dir, 'issues.md')}")
    say(f"  {os.path.join(out_dir, 'index.md')}")
    say(f"  {os.path.join(out_dir, 'index.html')}")
    say(f"  {os.path.join(out_dir, 'issues.csv')}")
    if args.open_report and not args.dry_run:
        webbrowser.open(f"file://{os.path.abspath(os.path.join(out_dir, 'index.html'))}")
    return 0 if ok == len(results) else 1


def cmd_personas(args: argparse.Namespace) -> int:
    personas = list_personas()
    if args.export:
        payload = {"personas": [p.to_dict() for p in personas]}
        with open(args.export, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
        say(f"wrote {len(personas)} personas to {args.export}")
        return 0
    for persona in personas:
        say(f"\n\033[1m{persona.id}\033[0m, {persona.name}")
        say(f"  {persona.blurb}")
        say(f"  device {persona.device} · tech {persona.tech_savvy} · patience {persona.patience}")
        if args.verbose:
            say("")
            for line in persona.prompt_block().splitlines():
                say(f"    {line}")
    say("")
    say("Use with:  uxprobe run --persona <id> --url ... --task \"...\"")
    say("Or all:    uxprobe run --persona all ...")
    return 0


def cmd_agents(_: argparse.Namespace) -> int:
    say("Backends (✓ = found on PATH):\n")
    for key, backend, present in available_backends():
        mark = "\033[32m✓\033[0m" if present else "\033[31m✗\033[0m"
        say(f" {mark} {key:<12} {backend.name}")
        if backend.notes:
            say(f"      {backend.notes}")
    say("\n ? custom       any CLI: --agent custom --cmd \"mycli -p {prompt}\"")
    say("\nA backend only helps if that CLI can reach a browser. For claude, that means the")
    say("Claude in Chrome extension or a Playwright MCP server; for others, an MCP browser")
    say("server configured in their own config file.")
    return 0


def cmd_init(args: argparse.Namespace) -> int:
    target = args.file or "study.yaml"
    if os.path.exists(target) and not args.force:
        say(f"error: {target} already exists (use --force to overwrite)")
        return 2
    with open(target, "w", encoding="utf-8") as handle:
        handle.write(EXAMPLE_STUDY)
    say(f"wrote {target}")
    say("edit it, then:  uxprobe study " + target)
    return 0


def _load_results(run_dir: str) -> list[RunResult]:
    results: list[RunResult] = []
    for path in sorted(glob.glob(os.path.join(run_dir, "*", "report.json"))):
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        spec = RunSpec(
            persona=Persona.from_dict(data.get("persona", {})),
            task=Task.from_dict(data.get("task", {})),
            agent=data.get("agent", ""),
            model=data.get("model", ""),
            attempt=data.get("attempt", 1),
        )
        results.append(
            RunResult(
                spec=spec,
                run_dir=os.path.dirname(path),
                ok=bool(data.get("ok")),
                report=data.get("report") or {},
                error=data.get("error", ""),
                started_at=data.get("started_at", ""),
                finished_at=data.get("finished_at", ""),
                duration_s=float(data.get("duration_s") or 0),
                exit_code=data.get("exit_code"),
                agent_meta=data.get("agent_meta") or {},
            )
        )
    return results


def cmd_report(args: argparse.Namespace) -> int:
    results = _load_results(args.run_dir)
    if not results:
        say(f"error: no report.json files under {args.run_dir}")
        return 2
    folder = os.path.basename(os.path.normpath(args.run_dir))
    # Folders are "<YYYYMMDD>-<HHMMSS>-<study>"; show just the study name in the title.
    name = re.sub(r"^\d{8}-\d{6}-", "", folder) or folder
    meta = {"study": name, "started_at": results[0].started_at, "sessions": len(results)}
    for result in results:  # per-session pages first, then the study index
        with open(os.path.join(result.run_dir, "report.md"), "w", encoding="utf-8") as handle:
            handle.write(render_run_markdown(result))
    write_study_reports(results, args.run_dir, name, meta)
    say(f"rebuilt reports for {len(results)} session(s) in {args.run_dir}")
    if args.open_report:
        webbrowser.open(f"file://{os.path.abspath(os.path.join(args.run_dir, 'index.html'))}")
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    """Did the issues we found last time actually go away?"""
    from .analysis import _overlap, _tokens, prioritise

    before = _load_results(args.before)
    after = _load_results(args.after)
    if not before or not after:
        say("error: both directories must contain session reports")
        return 2

    old_groups = prioritise(before)
    new_groups = prioritise(after)
    matched: set[int] = set()
    fixed, persisting = [], []

    for old in old_groups:
        best, best_score = None, 0.0
        for i, new in enumerate(new_groups):
            if i in matched:
                continue
            score = _overlap(_tokens(old), _tokens(new))
            if score >= 0.45 and score > best_score:
                best, best_score = i, score
        if best is None:
            fixed.append(old)
        else:
            matched.add(best)
            persisting.append((old, new_groups[best]))
    introduced = [g for i, g in enumerate(new_groups) if i not in matched]

    lines = [f"# Comparison: {os.path.basename(os.path.normpath(args.after))} "
             f"vs {os.path.basename(os.path.normpath(args.before))}", ""]
    lines += [f"<sub>{len(old_groups)} issues before, {len(new_groups)} after. Matching is "
              "textual, so check anything surprising by hand.</sub>", ""]

    def block(title: str, rows: list, render) -> None:
        # note: .extend, not `lines +=`, augmented assignment would rebind `lines` local
        lines.extend([f"## {title} ({len(rows)})", ""])
        if not rows:
            lines.extend(["_none_", ""])
            return
        lines.extend([render(r) for r in rows] + [""])

    block("Gone", fixed, lambda g: f"- ✅ **{g['severity']}**: {g['what']}")
    block("Still there", persisting,
          lambda pair: f"- ⚠️ **{pair[1]['severity']}**: {pair[1]['what']}"
                       + (f"  <sub>(was {pair[0]['severity']})</sub>"
                          if pair[0]["severity"] != pair[1]["severity"] else ""))
    block("New", introduced, lambda g: f"- 🆕 **{g['severity']}**: {g['what']}")

    text = "\n".join(lines)
    out_path = args.output or os.path.join(args.after, "comparison.md")
    with open(out_path, "w", encoding="utf-8") as handle:
        handle.write(text)

    say(f"gone: {len(fixed)}  ·  still there: {len(persisting)}  ·  new: {len(introduced)}")
    for group in fixed[:5]:
        say(f"  ✅ {group['what'][:88]}")
    for _, group in persisting[:5]:
        say(f"  ⚠️  {group['what'][:88]}")
    for group in introduced[:5]:
        say(f"  🆕 {group['what'][:88]}")
    say(f"\nwrote {out_path}")
    return 0


def cmd_synth(args: argparse.Namespace) -> int:
    results = _load_results(args.run_dir)
    if not results:
        say(f"error: no report.json files under {args.run_dir}")
        return 2
    payload = json.dumps(
        [
            {
                "persona": r.spec.persona.name,
                "persona_id": r.spec.persona.id,
                "device": r.spec.persona.device,
                "task": r.spec.task.title,
                "report": r.report,
            }
            for r in results
        ],
        indent=1,
        ensure_ascii=False,
    )
    prompt = build_synthesis_prompt(payload, args.context)
    try:
        backend = get_backend(args.agent or "claude", args.cmd)
    except AgentError as exc:
        say(f"error: {exc}")
        return 2
    say(f"synthesising {len(results)} session(s) with {args.agent or 'claude'} ...")
    invocation = run_agent(
        backend,
        prompt,
        model=args.model or "",
        yolo=args.yolo,
        timeout=args.timeout or 600,
        stdout_log=os.path.join(args.run_dir, "synthesis.log"),
        echo=args.echo,
    )
    text = (invocation.text or "").strip()
    if not text:
        say("error: the agent returned nothing, see synthesis.log")
        return 1
    path = os.path.join(args.run_dir, "findings.md")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text + "\n")
    say(f"wrote {path}")
    return 0


# --------------------------------------------------------------------------
# parser
# --------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="uxprobe",
        description="Drive a website with a coding-CLI agent role-playing a real user, "
                    "and log what they did, where they struggled and how it felt.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  uxprobe personas
  uxprobe agents
  uxprobe run --url https://example.com --task "Find out what this company sells" \\
              --persona first-timer --persona mobile-commuter --open
  uxprobe init study.yaml && uxprobe study study.yaml --echo
  uxprobe synth runs/20260816-101500-example-com
""",
    )
    parser.add_argument("--version", action="version", version=f"uxprobe {__version__}")
    subs = parser.add_subparsers(dest="command", required=True)

    # run
    run = subs.add_parser("run", help="one-off session(s) from the command line")
    run.add_argument("--url", default="", help="page the session starts on")
    run.add_argument("--task", dest="tasks", action="append", default=[],
                     help="what the user is trying to do; repeatable")
    run.add_argument("--persona", dest="personas", action="append", default=[],
                     help="built-in persona id, a persona file, or 'all'; repeatable")
    run.add_argument("--success", action="append", default=[],
                     help="a success criterion for the task(s); repeatable")
    run.add_argument("--name", default="", help="name for this study")
    run.add_argument("--repeat", type=int, default=1,
                     help="run each persona/task combination N times to see variance")
    run.add_argument("--max-steps", type=int, default=25,
                     help="how many interactions before the persona gives up")
    run.add_argument("--browser", choices=BROWSER_CHOICES, default="auto",
                     help="how the agent should drive the browser")
    run.add_argument("--no-screenshots", action="store_true")
    _add_agent_args(run)
    _add_output_args(run)
    run.set_defaults(func=cmd_run)

    # study
    study = subs.add_parser("study", help="run a study file (yaml or json)")
    study.add_argument("file")
    study.add_argument("--only", action="append", default=[],
                       help="restrict to these persona or task ids; repeatable")
    study.add_argument("--repeat", type=int, default=0)
    study.add_argument("--browser", choices=BROWSER_CHOICES, default=None)
    _add_agent_args(study)
    _add_output_args(study)
    study.set_defaults(func=cmd_study)

    # personas
    personas = subs.add_parser("personas", help="list the built-in personas")
    personas.add_argument("-v", "--verbose", action="store_true",
                          help="show the full prompt block for each")
    personas.add_argument("--export", default="", help="write them to a JSON file to edit")
    personas.set_defaults(func=cmd_personas)

    # agents
    agents = subs.add_parser("agents", help="list agent backends and whether they are installed")
    agents.set_defaults(func=cmd_agents)

    # init
    init = subs.add_parser("init", help="write an example study file")
    init.add_argument("file", nargs="?", default="study.yaml")
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=cmd_init)

    # report
    report = subs.add_parser("report", help="rebuild index.md / index.html from a run directory")
    report.add_argument("run_dir")
    report.add_argument("--open", dest="open_report", action="store_true")
    report.set_defaults(func=cmd_report)

    # compare
    compare = subs.add_parser(
        "compare", help="check which issues from an earlier study are gone, still there, or new")
    compare.add_argument("before", help="the earlier run directory")
    compare.add_argument("after", help="the later run directory")
    compare.add_argument("-o", "--output", default="", help="where to write comparison.md")
    compare.set_defaults(func=cmd_compare)

    # synth
    synth = subs.add_parser("synth", help="ask an agent to write a cross-session findings memo")
    synth.add_argument("run_dir")
    synth.add_argument("--context", default="", help="extra context about the product or study")
    synth.add_argument("--echo", action="store_true")
    _add_agent_args(synth)
    synth.set_defaults(func=cmd_synth)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if os.name == "nt":
        os.environ.setdefault("PYTHONUTF8", "1")
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    try:
        return args.func(args)
    except KeyboardInterrupt:
        say("\ninterrupted")
        return 130
    except (ConfigError, AgentError) as exc:
        say(f"error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
