#!/usr/bin/env python3
"""One command that proves the repository.

    python3 tools/check_all.py

Runs, in order, and stops at the first failure (exit code 1):
  1. tools/validate.py            the workflow files and map.yaml against SCHEMA.md
  2. tools/build.py               studio.html + build/studio.artifact.html (+ framework/steps.md via docs.py)
  3. tools/docs.py                framework/steps.md, standalone
  4. a check that studio.html makes no external requests and carries the JSON data block
  5. framework/tools/orchestrate.py check   every step has a role and mode, every command a real step
  6. the product-repository generators on a throwaway fixture tree:
       logic_index.py, components_index.py, decisions_index.py, install_commands.py (all agents, twice)
     the good fixture must pass; a fixture with a broken decision log must be refused.
  7. the runner (framework/tools/run.py) with the fake harness on the same fixture: a record
     started at define.intake is driven from define.sort through every PM stop (exit 3, a
     scripted answer each time) to deliver.done (exit 0); a stalled step is retried once,
     a step that never moves exits 4, a harness that answers the PM gate itself exits 4;
     run.py --dry-run and --check-harness fake.
  8. groups (PLAN 2026-09-11-breakdown §6.2–6.4), same fixture, fake harness: a large request
     → breakdown → confirm (yes) → spawn → three children → child 1 to deliver.done →
     run.py --group releases child 2 and stops at its discussion, QUEUE.md "1 of 3 delivered";
     a removal → impact (two dependants) → confirm (retire one, keep one) → breakdown with
     the replacement chunk first → spawn; and the refusals or states E1, E2, E3, E4, E5, E9,
     E10, E11, E15, E18, E20.
Stdlib only (plus PyYAML, which every tool here already needs).
"""
from __future__ import annotations
import re
import shutil
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable
FW_TOOLS = ROOT / "framework" / "tools"

GOOD_DECISION = """---
made_at: "2026-09-09T14:32+05:30"
category: backend
made_by: PM
at_step: deliver.approve-plan
nodes: [login]
---
# Use sessions

## Situation
We needed auth.

## Decision
Sessions.

## Reasons
- Instead of JWT, sessions are simpler.
"""


def step(title: str, argv: list[str], cwd: Path = ROOT, expect: int = 0) -> None:
    print(f"== {title}")
    r = subprocess.run(argv, cwd=cwd, capture_output=True, text=True)
    out = (r.stdout + r.stderr).rstrip()
    if out:
        print("   " + out.replace("\n", "\n   "))
    if "Traceback" in out:
        fail(f"{title}: crashed with a traceback")
    if r.returncode != expect:
        fail(f"{title}: exit code {r.returncode}, expected {expect}")


def fail(msg: str) -> None:
    print(f"\nFAIL — {msg}")
    sys.exit(1)


def fixture(root: Path) -> None:
    """A minimal product repository per framework/README.md."""
    (root / "logic" / "login").mkdir(parents=True)
    (root / "logic" / "login.md").write_text(
        "# Login\n\nStatus: delivered v1\n\n## Acceptance criteria\n- A valid password gets in\n", encoding="utf-8")
    (root / "logic" / "login" / "reset-password.md").write_text(
        "# Reset password\n\nStatus: approved, not yet delivered\n\n## Acceptance criteria\n- Email link\n", encoding="utf-8")
    (root / "code" / "backend" / "auth").mkdir(parents=True)
    (root / "code" / "backend" / "auth" / "auth.py").write_text("# @node login\n# @node reset-password\n", encoding="utf-8")
    (root / "decisions").mkdir()
    (root / "decisions" / "D-0001-sessions.md").write_text(GOOD_DECISION, encoding="utf-8")
    shutil.copytree(ROOT / "framework" / "commands", root / "framework" / "commands")
    shutil.copytree(FW_TOOLS, root / "framework" / "tools", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(ROOT / "framework" / "orchestration", root / "framework" / "orchestration")
    shutil.copytree(ROOT / "workflows", root / "framework" / "workflows")
    shutil.copy(ROOT / "framework" / "templates" / "AGENTS.md", root / "AGENTS.md")
    # names the toolbox's `enabled_when`, so the runner's toolbox rows (and the separate verify passes) are exercised
    (root / "architecture.md").write_text("# Architecture\n\nTools: python 3, pytest, ECC (toolbox).\nRun: python3 -m app\n", encoding="utf-8")


def runner_fixture(root: Path) -> None:
    """The runner with the fake harness: define.sort → every PM stop → deliver.done."""
    orch, run = str(root / "framework" / "tools" / "orchestrate.py"), str(root / "framework" / "tools" / "run.py")
    rec = "changes/2026-09-11-1-runner.md"
    fake = [PY, run, rec, "--harness", "fake"]
    step("runner: check-harness fake", [PY, run, "--check-harness", "--harness", "fake"], cwd=root)
    step("runner: start + the PM's intake answer", [PY, orch, "start", rec, "--command", "speckit.specify"], cwd=root)
    step("runner: intake answer", [PY, orch, "advance", rec, "--to", "sort", "--answer", "members can cancel within 7 days"], cwd=root)
    step("runner: dry run at define.sort", [PY, run, rec, "--harness", "fake", "--dry-run"], cwd=root)
    stops = [("define.discuss", ["--to", "write", "--when", "1", "--answer", "a cancel page"]),
             ("define.approve", ["--to", "commit", "--when", "3", "--answer", "yes"]),
             ("deliver.approve-plan", ["--to", "execute", "--when", "1", "--answer", "execute"]),
             ("deliver.accept", ["--to", "commit", "--when", "1", "--answer", "accepted"])]
    show = dict(os.environ, FAKE_HARNESS_SHOW_RUNMD="1")  # the fake echoes run.md as it stands mid-run into its log
    for pm_step, answer in stops:
        print(f"== runner: run to the PM stop {pm_step} (exit 3)")
        r = subprocess.run(fake, cwd=root, capture_output=True, text=True, env=show)
        print("   " + r.stdout.rstrip().replace("\n", "\n   "))
        if r.returncode != 3:
            fail(f"runner: expected exit 3 at {pm_step}, got {r.returncode}: {r.stderr[-300:]}")
        text = (root / rec).read_text(encoding="utf-8")
        if f"step: {pm_step}" not in text:
            fail(f"runner: the record is not at {pm_step}")
        if "Most common answer: --to" not in r.stdout or " && python3 framework/tools/run.py " not in r.stdout:
            fail(f"runner: the PM stop at {pm_step} does not name the most common answer with the paste-ready command")
        if not re.search(r"^\S+ · \S+ · fake · \d+:\d\d · moved$", r.stderr, re.M):
            fail(f"runner: no live status line with an outcome on stderr:\n{r.stderr}")
        step(f"runner: PM answers at {pm_step}", [PY, orch, "advance", rec] + answer, cwd=root)
    # run.md is written as the run goes: the challenge step's log shows the write step's row already there
    mid = (root / "changes" / "runs" / "2026-09-11-1-runner" / "4-define.challenge.log").read_text(encoding="utf-8")
    if "| 3 | define.write | Writer | fake |" not in mid or "| 4 | define.challenge | Challenger | fake | … | running since" not in mid:
        fail("runner: run.md did not carry the finished step's row and the in-flight row while the next step was running")
    print("== runner: run.md had the define.write row and the in-flight define.challenge row before the run ended")
    r = subprocess.run([PY, orch, "advance", rec, "--to", "1", "--answer", "yes"], cwd=root, capture_output=True, text=True)
    if r.returncode != 1 or "deliver.commit is an AI step, not a PM step; the runner (or the AI) moves it" not in r.stdout:
        fail(f"runner: advance --answer at an AI step must be refused as such (got {r.returncode}: {r.stdout[-200:]})")
    print("== runner: advance --answer at deliver.commit is refused as an AI step, before any --when complaint")
    step("runner: run to deliver.done (exit 0)", fake, cwd=root)
    text = (root / rec).read_text(encoding="utf-8")
    for needle in ("step: deliver.done", "## Findings — define.challenge", "## Findings — deliver.verify", "- [x] T001", "[security-reviewer]"):
        if needle not in text:
            fail(f"runner: the record lacks `{needle}`")
    logs = sorted(p.name for p in (root / "changes" / "runs" / "2026-09-11-1-runner").glob("*.log"))
    if len(logs) < 18 or "run.md" not in {p.name for p in (root / "changes" / "runs" / "2026-09-11-1-runner").iterdir()}:
        fail(f"runner: expected one log per step and run.md, got {logs}")
    run_md = (root / "changes" / "runs" / "2026-09-11-1-runner" / "run.md").read_text(encoding="utf-8")
    if "deliver.verify | Verifier | fake" not in run_md or "(4 sessions)" not in run_md:
        fail("runner: run.md does not show the four separate verify sessions")
    # a stalled step is retried once; a step that never moves is exit 4
    rec2 = "changes/2026-09-11-2-stall.md"
    step("runner: second record", [PY, orch, "start", rec2, "--command", "speckit.specify"], cwd=root)
    step("runner: intake answer", [PY, orch, "advance", rec2, "--to", "sort", "--answer", "x"], cwd=root)
    env = dict(os.environ, FAKE_HARNESS_STALL="define.sort")
    r = subprocess.run([PY, run, rec2, "--harness", "fake"], cwd=root, capture_output=True, text=True, env=env)
    log = (root / "changes" / "runs" / "2026-09-11-2-stall" / "1-define.sort.log").read_text(encoding="utf-8")
    if r.returncode != 3 or "## attempt 2" not in log or "previous attempt did not move the record" not in log:
        fail(f"runner: a stalled step was not retried once (exit {r.returncode})")
    print("== runner: a stalled define.sort was retried once and moved (exit 3 at define.discuss)")
    env = dict(os.environ, FAKE_HARNESS_STALL="always")
    step("runner: PM answers", [PY, orch, "advance", rec2, "--to", "write", "--when", "1", "--answer", "y"], cwd=root)
    r = subprocess.run([PY, run, rec2, "--harness", "fake"], cwd=root, capture_output=True, text=True, env=env)
    if r.returncode != 4 or "did not move the record after a retry" not in r.stdout:
        fail(f"runner: a step that never moves must exit 4 (got {r.returncode}: {r.stdout[-300:]})")
    print("== runner: a step that never moves exits 4 with the log path")
    # a harness that answers the PM step it landed on is refused: the runner checks the history, not the step
    env = dict(os.environ, FAKE_HARNESS_OVERSTEP="define.challenge")
    r = subprocess.run([PY, run, rec2, "--harness", "fake"], cwd=root, capture_output=True, text=True, env=env)
    if r.returncode != 4 or "answered the PM step define.approve itself" not in r.stdout:
        fail(f"runner: a harness that answered the PM gate itself must exit 4 (got {r.returncode}: {r.stdout[-300:]})")
    print("== runner: a harness that answered define.approve itself exits 4 (the gate is not skipped silently)")
    step("runner: orchestrate start refuses the meta command", [PY, orch, "start", rec2, "--command", "speckit.run"], cwd=root, expect=1)


def group_fixture(root: Path) -> None:
    """Step 8: large requests and removals with the fake harness (PLAN 2026-09-11-breakdown §6.2–6.4)."""
    orch, run, fake_py = str(root / "framework" / "tools" / "orchestrate.py"), str(root / "framework" / "tools" / "run.py"), str(root / "framework" / "tools" / "fake_harness.py")
    queue = root / "changes" / "QUEUE.md"

    def sh(argv, env=None):
        r = subprocess.run(argv, cwd=root, capture_output=True, text=True, env=env)
        if "Traceback" in r.stdout + r.stderr:
            fail(f"group: crashed with a traceback: {(r.stdout + r.stderr)[-400:]}")
        return r

    def pm(rec: str, *answer):
        step(f"group: PM answers at {rec}: {' '.join(answer)}", [PY, orch, "advance", rec] + list(answer), cwd=root)

    def runner(title: str, argv, expect: int, must=(), env=None, forbid=()):
        print(f"== group: {title} (exit {expect})")
        r = sh([PY, run] + list(argv) + ["--harness", "fake"], env=env)
        print("   " + r.stdout.rstrip().replace("\n", "\n   "))
        if r.returncode != expect:
            fail(f"group: {title}: expected exit {expect}, got {r.returncode}: {(r.stdout + r.stderr)[-400:]}")
        for needle in must:
            if needle not in r.stdout:
                fail(f"group: {title}: the runner's output lacks `{needle}`")
        for needle in forbid:
            if needle in r.stdout:
                fail(f"group: {title}: the runner's output must not contain `{needle}`")
        return r

    def refused(title: str, argv, needle: str, env=None):
        r = sh(argv, env=env)
        out = (r.stdout + r.stderr).strip()
        print(f"== group: {title}\n   {out.splitlines()[-1] if out else '(no output)'}")
        if r.returncode != 1 or needle not in out:
            fail(f"group: {title}: expected a refusal naming `{needle}` (exit 1), got {r.returncode}: {out[-400:]}")

    def text(rec: str) -> str:
        return (root / rec).read_text(encoding="utf-8")

    def at(rec: str, step_ref: str):
        if f"step: {step_ref}" not in text(rec):
            fail(f"group: {rec} is not at {step_ref}")

    def block(parent: str) -> str:
        m = re.search(rf"<!-- group: {re.escape(parent)} -->.*?<!-- /group -->", queue.read_text(encoding="utf-8"), re.S)
        return m.group(0) if m else ""

    def new_request(rec: str, words: str):
        step(f"group: start {rec}", [PY, orch, "start", rec, "--command", "speckit.specify"], cwd=root)
        step("group: intake answer", [PY, orch, "advance", rec, "--to", "sort", "--answer", words], cwd=root)
        runner(f"{rec} sort → discuss", [rec], 3, must=["PM step: define.discuss"])

    to_done = [("define.approve", ["--to", "commit", "--when", "3", "--answer", "yes"]),
               ("deliver.approve-plan", ["--to", "execute", "--when", "1", "--answer", "execute"]),
               ("deliver.accept", ["--to", "commit", "--when", "1", "--answer", "accepted"])]

    # (a) the large request: breakdown → confirm (yes) → spawn → three children → child 1 delivered → --group releases child 2
    P = "changes/2026-09-11-3-habit-tracker.md"
    C = [f"changes/2026-09-11-3.{n}-habit-tracker-{s}.md" for n, s in ((1, "log"), (2, "streak"), (3, "remind"))]
    new_request(P, "a habit tracker: log a habit, see a weekly streak, get a reminder")
    pm(P, "--to", "breakdown", "--when", "2", "--answer", "three capabilities: log, streak, reminder; propose the chunks")
    runner("breakdown (fake) → the PM stop at confirm-breakdown", [P], 3,
           must=["PM step: define.confirm-breakdown", "Most common answer: --to 1 --when 1", '--answer "yes" && python3 framework/tools/run.py '])
    body = text(P)
    for needle in ("## Breakdown — proposed", "1. habit-tracker-log", "3. habit-tracker-remind", "depends on: chunk 1", "Order and reasons:", "Alternatives considered:"):
        if needle not in body:
            fail(f"group: the fake's breakdown block lacks `{needle}`")
    if "## Breakdown — PM answer" in body:
        fail("group: the fake answered the PM gate itself")
    pm(P, "--to", "spawn", "--when", "1", "--answer", "yes")
    runner("spawn (fake) → broken-down", [P], 0, must=["closed at define.broken-down", "0 of 3 delivered; in flight: chunk 1"])
    for c in C:
        if not (root / c).is_file():
            fail(f"group: spawn did not write {c}")
    at(C[0], "define.discuss"); at(C[1], "waiting"); at(C[2], "waiting")
    # E9, E10, --group on a non-parent
    runner("E9: the runner on the waiting child 2", [C[1]], 3, must=[f"Waiting: chunk 2 of {P} waits for chunk 1 ({C[0]} at define.discuss) to reach deliver.done"])
    refused("E10: start on a child", [PY, orch, "start", C[1], "--command", "speckit.specify"], "children are created by define.spawn; run the parent (E10)")
    runner("--group on a child is refused", ["--group", C[0]], 4, must=["names a child (chunk 1 of", f"pass its parent: --group {P}"])
    runner("--group on a record with no children is refused", ["--group", "changes/2026-09-11-1-runner.md"], 4, must=["names a record with no children"])
    # child 1 to deliver.done, the PM's answers scripted as in step 7; without --group the run stops when the child closes
    pm(C[0], "--to", "write", "--when", "1", "--answer", "a log page")
    for pm_step, answer in to_done:
        runner(f"child 1 to the PM stop {pm_step}", [C[0]], 3, must=[f"PM step: {pm_step}", "Group: "])
        pm(C[0], *answer)
    runner("child 1 to deliver.done (no --group: stops after the child)", [C[0]], 0, must=["closed at deliver.done", "1 of 3 delivered; nothing in flight"], forbid=["released"])
    at(C[0], "deliver.done"); at(C[1], "waiting")
    runner("--group continues: releases child 2 and stops at its discussion", ["--group", P], 3,
           must=[f"group: released chunk 2 ({C[1]})", f"group: running {C[1]}", "PM step: define.discuss", f"Then run again: python3 framework/tools/run.py --group {P}"])
    at(C[1], "define.discuss")
    if "1 of 3 delivered; in flight: chunk 2" not in block(P) or f"| 1 | {C[0]} | deliver.done | nobody |" not in block(P):
        fail(f"group: QUEUE.md does not show 1 of 3 delivered with child 2 in flight:\n{block(P)}")
    print("== group: QUEUE.md shows \"1 of 3 delivered; in flight: chunk 2\"")
    # E3: child 2 dropped at its own gate; --group goes on with chunk 3
    pm(C[1], "--to", "drop", "--when", "8", "--answer", "stop, the streak is not wanted")
    runner("E3: --group drops chunk 2 and releases chunk 3", ["--group", P], 3, must=["closed at define.dropped", f"group: released chunk 3 ({C[2]})", "PM step: define.discuss"])
    if "1 of 3 delivered; 1 dropped; in flight: chunk 3" not in block(P):
        fail(f"group: QUEUE.md after the drop:\n{block(P)}")
    print("== group: E3: QUEUE.md shows \"1 of 3 delivered; 1 dropped; in flight: chunk 3\"")
    # E4: revise-breakdown from chunk 3; the parent reopens; yes → spawn reconciles; the delivered chunk is untouched
    step("group: E4: the fake writes chunk 3's discussion (a proposed correction)", [PY, fake_py, "--discuss", C[2]], cwd=root)
    before = (root / C[0]).read_bytes()
    pm(C[2], "--to", "revise-breakdown", "--when", "4", "--answer", "building this showed a settings capability is missing")
    at(C[2], "define.revise-breakdown")
    runner("E4: --group runs the parent, reopened at confirm-breakdown", ["--group", P], 3, must=["PM step: define.confirm-breakdown", "Most common answer: --to 1 --when 1"])
    if "## Breakdown — previous chunks" not in text(P):
        fail("group: E4: the parent does not show the previous chunks beside the proposal")
    pm(P, "--to", "spawn", "--when", "1", "--answer", "yes")
    S4 = "changes/2026-09-11-3.3-habit-tracker-settings.md"
    runner("E4: --group spawns the revised set and releases the next chunk", ["--group", P], 3,
           must=["closed at define.broken-down", f"group: released chunk 2 ({C[2]})", "PM step: define.discuss"])
    if (root / C[0]).read_bytes() != before:
        fail("group: E4: the delivered chunk 1 was touched by the revision")
    at(C[0], "deliver.done"); at(C[2], "define.discuss"); at(S4, "waiting")
    if "1 of 4 delivered; 1 dropped; in flight: chunk 2" not in block(P) or f"| 3 | {S4} | waiting | chunk 2 |" not in block(P):
        fail(f"group: E4: QUEUE.md after the revision:\n{block(P)}")
    print("== group: E4: chunk 1 untouched (bytes equal, deliver.done); the new chunk waits on chunk 2; two breakdown decisions")
    decs = sorted((root / "decisions").glob("D-*-breakdown-habit-tracker.md"))
    if len(decs) != 2 or "supersedes: " not in decs[1].read_text(encoding="utf-8") or "superseded_by: " not in decs[0].read_text(encoding="utf-8"):
        fail("group: E4: expected two breakdown decisions, the second superseding the first")
    # E11: the parent missing, then its PM-answer block missing
    (root / P).rename(root / "changes" / "parked.tmp")
    refused("E11: next on a child whose parent file is missing", [PY, orch, "next", C[2]], f"{P}, which does not exist (E11)")
    (root / "changes" / "parked.tmp").rename(root / P)
    (root / P).write_text(text(P).replace("## Breakdown — PM answer", "## Breakdown — answer"), encoding="utf-8")
    refused("E11: check on a child whose parent lost its PM-answer block", [PY, orch, "check", C[2]], "has no `## Breakdown — PM answer` block (E11)")
    (root / P).write_text(text(P).replace("## Breakdown — answer", "## Breakdown — PM answer"), encoding="utf-8")
    step("group: check on the child again", [PY, orch, "check", C[2]], cwd=root)

    # (b) the removal: impact (two dependants from the tags) → confirm (retire one, keep one) → breakdown, replacement first → spawn
    R = "changes/2026-09-11-4-remove-reminders.md"
    new_request(R, "remove `reminder`, nobody uses it")
    pm(R, "--to", "impact", "--when", "3", "--answer", "show me the repercussions")
    runner("impact (fake) → the PM stop at confirm-impact", [R], 3,
           must=["PM step: define.confirm-impact", "Most common answer: --to 1 --when 1", "proceed with the chosen set", "<dependant>: retire it too"])
    body = text(R)
    for needle in ("## Impact — proposed", "Removing or changing: reminder", "1. login [tags: code/backend/auth/auth.py", "2. reset-password [tags:",
                   "options: retire it too | keep it by", "recommended:", "Stored data: reminder table — keep | migrate", "recommended: keep"):
        if needle not in body:
            fail(f"group: the fake's impact block lacks `{needle}`")
    if "## Impact — PM answer" in body:
        fail("group: the fake answered the PM gate itself")
    pm(R, "--to", "breakdown", "--when", "3", "--answer", "login: retire it too; reset-password: keep it by a replacement; reminder table: keep")
    runner("breakdown after the impact answer: the replacement chunk before the removal", [R], 3, must=["PM step: define.confirm-breakdown"])
    body = text(R)
    i, j = body.find("1. remove-reminders-replacement"), body.find("2. remove-reminders-removal")
    if i < 0 or j < 0 or j < i or "depends on: chunk 1" not in body[j:]:
        fail("group: the breakdown after an impact answer must list the replacement chunk before the removal chunk, the removal depending on it")
    pm(R, "--to", "spawn", "--when", "1", "--answer", "yes")
    runner("--group on the parent at spawn: spawns, then runs chunk 1 to its discussion", ["--group", R], 3, must=["closed at define.broken-down", "PM step: define.discuss"])
    RC = ["changes/2026-09-11-4.1-remove-reminders-replacement.md", "changes/2026-09-11-4.2-remove-reminders-removal.md"]
    if f"| 1 | {RC[0]} | define.discuss | PM |" not in block(R) or f"| 2 | {RC[1]} | waiting | chunk 1 |" not in block(R):
        fail(f"group: the removal group does not show the replacement first:\n{block(R)}")
    print("== group: the removal group shows the replacement chunk first, the removal waiting on it")

    # E1: one thing after all
    P1 = "changes/2026-09-11-5-reports.md"
    new_request(P1, "reports: daily, weekly, monthly")
    pm(P1, "--to", "breakdown", "--when", "2", "--answer", "propose the chunks")
    runner("E1: breakdown → confirm-breakdown", [P1], 3, must=["PM step: define.confirm-breakdown"])
    pm(P1, "--to", "write", "--when", "3", "--answer", "one thing")
    runner("E1: write as a single node → the PM stop at approve", [P1], 3, must=["PM step: define.approve"])
    if "## Breakdown — proposed" not in text(P1) or "## define.write" not in text(P1):
        fail("group: E1: the proposal must stay as history and the node be written")
    print("== group: E1: single node written; the proposal stays in the record")
    # E2: three rounds, then only write or drop
    P2 = "changes/2026-09-11-6-accounts.md"
    new_request(P2, "accounts: sign up, log in, reset the password")
    pm(P2, "--to", "breakdown", "--when", "2", "--answer", "propose the chunks")
    runner("E2: round 1", [P2], 3, must=["PM step: define.confirm-breakdown"])
    for n in (1, 2):
        pm(P2, "--to", "breakdown", "--when", "2", "--answer", f"merge 1 and 2, round {n}")
        runner(f"E2: rewrite after the PM's words, round {n}", [P2], 3, must=["PM step: define.confirm-breakdown"])
    if text(P2).count("## Breakdown — proposed") != 3 or "Rewritten from the PM's words: merge 1 and 2, round 2" not in text(P2):
        fail("group: E2: expected three proposed blocks, the last rewritten from the PM's words")
    refused("E2: a yes after three rounds", [PY, orch, "advance", P2, "--to", "spawn", "--when", "1", "--answer", "yes"], "proposed 3 times (the cap is 3); only write (one node) or drop")
    refused("E2: a fourth rewrite", [PY, orch, "advance", P2, "--to", "breakdown", "--when", "2", "--answer", "split again"], "the cap is 3")
    pm(P2, "--to", "drop", "--when", "4", "--answer", "stop")
    # E5: two chunks on one node with no dependency
    P5 = "changes/2026-09-11-7-shop.md"
    new_request(P5, "a shop: catalogue, basket, checkout")
    pm(P5, "--to", "breakdown", "--when", "2", "--answer", "propose the chunks")
    runner("E5: a breakdown whose chunks 2 and 3 share a node", [P5], 3, must=["PM step: define.confirm-breakdown"], env=dict(os.environ, FAKE_HARNESS_E5="1"))
    pm(P5, "--to", "spawn", "--when", "1", "--answer", "yes")
    refused("E5: spawn refuses", [PY, orch, "advance", P5, "--to", "broken-down"], "both touch node shop-streak with no dependency between them (E5)")
    # E18: a dependant mid-Deliver; then the impact once that record is gone; E20: the challenge reports a tagged dependant the block omits
    R2 = "changes/2026-09-11-8-remove-login.md"
    new_request(R2, "remove `login`")
    (root / R2).write_text(text(R2).replace("command: speckit.specify", "command: speckit.specify\nnodes: [login]", 1), encoding="utf-8")
    busy = root / "changes" / "2026-09-10-9-build-login.md"
    busy.write_text("---\nstep: deliver.execute\nmode: agent\nnodes: [login]\n---\n# Build login\n", encoding="utf-8")
    refused("E18: impact while a record in Deliver names the node", [PY, orch, "advance", R2, "--to", "impact", "--when", "3", "--answer", "show"],
            "is in Deliver (deliver.execute) on node login, which this request names (E18)")
    busy.unlink()
    pm(R2, "--to", "impact", "--when", "3", "--answer", "show")
    runner("E18 lifted: impact → confirm-impact", [R2], 3, must=["PM step: define.confirm-impact"])
    pm(R2, "--to", "write", "--when", "1", "--answer", "reset-password: keep it by a replacement; login table: keep")
    (root / "code" / "backend" / "notify").mkdir()
    (root / "code" / "backend" / "notify" / "notify.py").write_text("# @node notification-settings\n", encoding="utf-8")
    runner("E20: write → challenge finds the tagged dependant the impact block omits", [R2], 3, must=["PM step: define.approve"])
    finding = "the impact block omits the tagged dependant `notification-settings` (@node notification-settings in code/backend/notify/notify.py)"
    if finding not in text(R2):
        fail("group: E20: the challenge did not report the omitted dependant")
    print(f"== group: E20: finding present: {finding}")
    shutil.rmtree(root / "code" / "backend" / "notify")
    # E15: a removal with no dependants has no impact stop
    R3 = "changes/2026-09-11-9-remove-orphan.md"
    new_request(R3, "remove `orphan`")
    pm(R3, "--to", "impact", "--when", "3", "--answer", "show")
    r = runner("E15: the impact block lists no dependants; leaving impact is refused", [R3], 4, must=["did not move the record"], env=dict(os.environ, FAKE_HARNESS_NO_DEPENDANTS="1"))
    log = re.search(r"see (\S+\.log)", r.stdout)
    if not log or "with no dependants there is no impact stop (E15)" not in (root / log.group(1)).read_text(encoding="utf-8"):
        fail("group: E15: the refusal naming E15 is not in the step log")
    print("== group: E15: refused with \"no dependants … there is no impact stop (E15)\"")
    R4 = "changes/2026-09-11-10-retire-orphan.md"
    new_request(R4, "remove `orphan`, no dependants found (tags, tree, glossary)")
    pm(R4, "--to", "write", "--when", "1", "--answer", "no dependants found (tags, tree, glossary): retire it")
    runner("E15: the same removal goes discuss → write, as today", [R4], 3, must=["PM step: define.approve"])

    # Phase 6 (the challenger's cases, test-cases.md T91+): the hand-released child, spawn twice, a chunk mid-Deliver under a
    # revision, the reopened gate's write/drop, the stores of an impact answer, E18 from task tags, slugs and order, QUEUE.md by hand
    def edit(rec: str, old: str, new: str):
        (root / rec).write_text(text(rec).replace(old, new, 1), encoding="utf-8")

    F = "changes/2026-09-11-11-fleet.md"
    FC = [f"changes/2026-09-11-11.{n}-fleet-{s}.md" for n, s in ((1, "log"), (2, "streak"), (3, "remind"))]
    new_request(F, "a fleet: vehicles, drivers, trips")
    pm(F, "--to", "breakdown", "--when", "2", "--answer", "propose the chunks")
    runner("C1: breakdown → confirm-breakdown", [F], 3, must=["PM step: define.confirm-breakdown"])
    pm(F, "--to", "spawn", "--when", "1", "--answer", "Yes.")
    runner("C1: a yes with punctuation spawns", [F], 0, must=["closed at define.broken-down"])
    edit(FC[1], "step: waiting", "step: define.discuss"); edit(FC[1], "mode: waiting", "mode: pm")
    refused("C1: a child whose step was set to define.discuss by hand while chunk 1 is open", [PY, orch, "next", FC[1]], "the record was edited by hand; set `step: waiting` and `mode: waiting` back")
    refused("C1: advance on it is refused the same way", [PY, orch, "advance", FC[1], "--to", "write", "--when", "1", "--answer", "x"], "set `step: waiting` and `mode: waiting` back")
    edit(FC[1], "step: define.discuss", "step: waiting"); edit(FC[1], "mode: pm", "mode: waiting")
    step("group: C1: restored, next on the child is a wait again", [PY, orch, "next", FC[1]], cwd=root)
    edit(F, "step: define.broken-down", "step: define.spawn")
    refused("C2: spawn twice (the parent's step set back to define.spawn by hand)", [PY, orch, "advance", F, "--to", "broken-down"], "was already spawned (1 spawn(s) for 1 yes(es) in the history")
    edit(F, "step: define.spawn", "step: define.broken-down")
    if len(sorted((root / "decisions").glob("D-*-breakdown-fleet.md"))) != 1 or text(FC[0]).count("to: define.discuss") != 1:
        fail("C2: a refused second spawn must leave one decision and one spawn edge on chunk 1")
    print("== group: C2: one breakdown decision, one spawn edge on chunk 1")
    pm(FC[0], "--to", "write", "--when", "1", "--answer", "a vehicles page")
    for pm_step, answer in to_done:
        runner(f"C3: chunk 1 to the PM stop {pm_step}", [FC[0]], 3, must=[f"PM step: {pm_step}"])
        pm(FC[0], *answer)
    runner("C3: chunk 1 to deliver.done; --group releases chunk 2", ["--group", F], 3, must=["closed at deliver.done", f"group: released chunk 2 ({FC[1]})", "PM step: define.discuss"])
    pm(FC[1], "--to", "write", "--when", "1", "--answer", "a drivers page")
    for pm_step, answer in to_done[:2]:
        runner(f"C3: chunk 2 to the PM stop {pm_step}", [FC[1]], 3, must=[f"PM step: {pm_step}"])
        pm(FC[1], *answer)
    at(FC[1], "deliver.execute")
    step("group: C3: chunk 3 released (its dependency, chunk 1, is delivered) while chunk 2 is mid-Deliver", [PY, orch, "advance", FC[2], "--to", "define.discuss"], cwd=root)
    step("group: C3: the fake writes chunk 3's discussion (a proposed correction keeping chunk 2)", [PY, fake_py, "--discuss", FC[2]], cwd=root)
    mid = (root / FC[1]).read_bytes()
    pm(FC[2], "--to", "revise-breakdown", "--when", "4", "--answer", "a settings chunk is missing")
    refused("C4: the reopened parent cannot take write while it has children", [PY, orch, "advance", F, "--to", "write", "--when", "3", "--answer", "one thing"], "has children (the group block in changes/QUEUE.md)")
    refused("C4: nor drop", [PY, orch, "advance", F, "--to", "drop", "--when", "4", "--answer", "stop"], "has children (the group block in changes/QUEUE.md)")
    pm(F, "--to", "spawn", "--when", "1", "--answer", "yes")
    step("group: C3: the re-spawn keeps the chunk mid-Deliver untouched", [PY, orch, "advance", F, "--to", "broken-down"], cwd=root)
    S = "changes/2026-09-11-11.4-fleet-settings.md"
    at(FC[1], "deliver.execute"); at(FC[2], "waiting"); at(S, "waiting")
    if (root / FC[1]).read_bytes() != mid:
        fail("C3: the re-spawn rewrote a chunk mid-Deliver")
    print("== group: C3: chunk 2 still at deliver.execute, bytes equal; chunk 3 and the new settings chunk re-planned around it")
    # C4: a revision that removes the chunk mid-Deliver is refused at spawn until that chunk closes
    step("group: C4: chunk 3 released again", [PY, orch, "advance", FC[2], "--to", "define.discuss"], cwd=root)
    (root / FC[2]).write_text(text(FC[2]) + "\n## define.discuss\n\nBuilding chunk 2 showed the drivers chunk is not wanted. Proposed correction:\nChunks:\n"
                              "  1. fleet-log — vehicles (`fleet-log`)\n     depends on: none\n     why this line: kept\n"
                              "  2. fleet-remind — trips (`fleet-remind`)\n     depends on: chunk 1\n     why this line: kept\n"
                              "  3. fleet-settings — settings (`fleet-settings`)\n     depends on: chunk 2\n     why this line: kept\n"
                              "Order and reasons: as before\nNot split further because: one capability each\nAlternatives considered: keep the drivers chunk\n", encoding="utf-8")
    print("== group: C4: chunk 3's second discussion (the newest `## define.discuss` drives the revision) drops the drivers chunk, which is mid-Deliver")
    pm(FC[2], "--to", "revise-breakdown", "--when", "4", "--answer", "drop the drivers chunk")
    pm(F, "--to", "spawn", "--when", "1", "--answer", "yes")
    refused("C4: a revision that removes the chunk mid-Deliver is refused at spawn", [PY, orch, "advance", F, "--to", "broken-down"], "is in Deliver (deliver.execute")
    at(FC[1], "deliver.execute")
    runner("C4: chunk 2 runs on to deliver.accept", [FC[1]], 3, must=["PM step: deliver.accept"])
    pm(FC[1], "--to", "commit", "--when", "1", "--answer", "accepted")
    runner("C4: chunk 2 to deliver.done", [FC[1]], 0, must=["closed at deliver.done"])
    step("group: C4: the same revision spawns once chunk 2 is delivered (a delivered chunk is never touched)", [PY, orch, "advance", F, "--to", "broken-down"], cwd=root)
    at(FC[1], "deliver.done"); at(FC[2], "waiting"); at(S, "waiting")
    if "| 2 | " + FC[2] not in block(F) or "2 of 4 delivered" not in block(F):
        fail(f"C4: the group block after the revision:\n{block(F)}")
    print("== group: C4: chunk 2 delivered and kept; remind is now chunk 2, settings chunk 3; \"2 of 4 delivered\"")
    # C5: the impact answer must name every store; the pasted placeholder is refused; E19: a block recommending delete cannot leave impact
    R5 = "changes/2026-09-11-12-remove-reset.md"
    new_request(R5, "remove `reset-password`")
    pm(R5, "--to", "impact", "--when", "3", "--answer", "show")
    runner("C5: impact → confirm-impact", [R5], 3, must=["PM step: define.confirm-impact"])
    refused("C5: the pasted placeholder from the PM stop is refused", [PY, orch, "advance", R5, "--to", "1", "--when", "1", "--answer",
             "<dependant>: retire it too | keep it by <replacement> | narrow the removal to <…> | postpone; <store>: keep | migrate | delete"], "names no choice for dependant 'login'")
    refused("C5: an answer naming every dependant but not the store", [PY, orch, "advance", R5, "--to", "1", "--when", "1", "--answer", "login: retire it too"],
            "names no choice for the stored data 'reset_password table'")
    pm(R5, "--to", "write", "--when", "1", "--answer", "login: retire it too; reset_password table: migrate to the audit log")
    R6 = "changes/2026-09-11-13-remove-orphan2.md"
    new_request(R6, "remove `orphan2`")
    pm(R6, "--to", "impact", "--when", "3", "--answer", "show")
    (root / R6).write_text(text(R6) + "\n## Impact — proposed 2026-09-11\n\nRemoving or changing: orphan2 — x\nDependants (source in brackets):\n  1. login [tags: code/backend/auth/auth.py]\n     options: retire it too | keep it by a replacement | narrow the removal to x | postpone\n     recommended: retire it too — y\nRules and decisions affected: none\nStored data: orphan2 table — keep | migrate to x | delete; recommended: delete\nPossible, unverified: none\n", encoding="utf-8")
    refused("C5: E19: an impact block recommending delete for a store cannot leave impact", [PY, orch, "advance", R6, "--to", "confirm-impact"], "\"delete\" is never the default (E19)")
    # C6: E18 from a task line's tag, with no `nodes:` anywhere; the removal names the node in backticks
    R7 = "changes/2026-09-11-14-remove-login2.md"
    new_request(R7, "remove `login`, the SSO replaces it")
    busy = root / "changes" / "2026-09-10-8-build-login.md"
    busy.write_text("---\nstep: deliver.execute\nmode: agent\n---\n# Build login\n\n## Tasks\n- [ ] T001 [P] [login] write the component\n", encoding="utf-8")
    refused("C6: E18 from a task tag `[login]` on a record in Deliver with no `nodes:`", [PY, orch, "advance", R7, "--to", "impact", "--when", "3", "--answer", "show"],
            "2026-09-10-8-build-login.md is in Deliver (deliver.execute) on node login, which this request names (E18)")
    busy.write_text("---\nstep: deliver.execute\nmode: agent\n---\n# Build login\n\nthe plan talks about `login` in prose only\n", encoding="utf-8")
    pm(R7, "--to", "impact", "--when", "3", "--answer", "show")
    print("== group: C6: a record in Deliver naming the node only in prose is not compared (the refusal text states the heuristic)")
    busy.unlink()
    # C7: a chunk slug with a path part, and a chunk depending on a later chunk, cannot leave breakdown
    P7 = "changes/2026-09-11-15-inventory.md"
    new_request(P7, "inventory: stock, orders, suppliers")
    pm(P7, "--to", "breakdown", "--when", "2", "--answer", "propose the chunks")
    runner("C7: breakdown → confirm-breakdown", [P7], 3, must=["PM step: define.confirm-breakdown"])
    edit(P7, "step: define.confirm-breakdown", "step: define.breakdown"); edit(P7, "mode: pm", "mode: agent")
    edit(P7, "1. inventory-log", "1. ../../etc/inventory-log")
    refused("C7: a slug with a path part cannot leave breakdown", [PY, orch, "advance", P7, "--to", "confirm-breakdown"], "cannot name a record file")
    edit(P7, "1. ../../etc/inventory-log", "1. inventory-log")
    edit(P7, "depends on: none\n     why this line: reads the log", "depends on: chunk 3\n     why this line: reads the log")
    refused("C7: a chunk depending on a later chunk cannot leave breakdown", [PY, orch, "advance", P7, "--to", "confirm-breakdown"], "which comes after it; dependencies first")
    edit(P7, "depends on: chunk 3\n     why this line: reads the log", "depends on: none\n     why this line: reads the log")
    (root / P7).write_text(text(P7) + "\n## Breakdown — PM answer 2026-09-11\n\nyes\n", encoding="utf-8")
    refused("C7: a `## Breakdown — PM answer` block the AI wrote (no gate exit in the history) cannot leave breakdown", [PY, orch, "advance", P7, "--to", "confirm-breakdown"],
            "carries 1 `## Breakdown — PM answer` block(s) but the PM has answered define.confirm-breakdown 0 time(s)")
    # C8: QUEUE.md edited by hand: the fleet block's closing fence removed; the next move rewrites it and keeps the other groups
    q = queue.read_text(encoding="utf-8")
    i = q.find(f"<!-- group: {F} -->"); j = q.find("<!-- /group -->", i)
    queue.write_text(q[:j] + q[j + len("<!-- /group -->"):], encoding="utf-8")
    step("group: C8: a child move after the fence was removed by hand", [PY, orch, "advance", FC[2], "--to", "define.discuss"], cwd=root)
    q = queue.read_text(encoding="utf-8")
    if q.count(f"<!-- group: {F} -->") != 1 or not block(F) or f"| 2 | {FC[2]} | define.discuss |" not in block(F) or not block(P) or not block(R):
        fail(f"C8: QUEUE.md after the hand edit:\n{q}")
    print("== group: C8: the fleet block was rewritten with its fence; the other group blocks are intact")
    # C9: a dropped middle chunk hands its dependency on (chain 1 → 2 → 3, chunk 2 dropped by hand while chunk 1 is open)
    P9 = "changes/2026-09-11-16-billing.md"
    new_request(P9, "billing: invoices, payments, refunds")
    pm(P9, "--to", "breakdown", "--when", "2", "--answer", "propose the chunks")
    runner("C9: breakdown → confirm-breakdown", [P9], 3, must=["PM step: define.confirm-breakdown"])
    edit(P9, "depends on: chunk 1\n", "depends on: chunk 2\n")
    pm(P9, "--to", "spawn", "--when", "1", "--answer", "yes")
    runner("C9: spawn", [P9], 0, must=["closed at define.broken-down"])
    B2, B3 = "changes/2026-09-11-16.2-billing-streak.md", "changes/2026-09-11-16.3-billing-remind.md"
    edit(B2, "step: waiting", "step: define.dropped"); edit(B2, "mode: waiting", "mode: closed")
    refused("C9: chunk 3 (depends on the dropped chunk 2, which depended on chunk 1) still waits on chunk 1", [PY, orch, "advance", B3, "--to", "define.discuss"], "chunk 3 waits on chunk 1")


def check_studio_html() -> None:
    print("== studio.html: self-contained")
    html = (ROOT / "studio.html").read_text(encoding="utf-8")
    ext = [u for u in re.findall(r"""(?:src|href)\s*=\s*["']([^"']+)""", html) if re.match(r"^(https?:)?//", u)]
    ext += re.findall(r"@import\s+url\(", html) + re.findall(r"url\(\s*['\"]?https?://", html)
    if ext:
        fail(f"studio.html requests external resources: {ext}")
    if html.count('<script type="application/json" id="data">') != 1:
        fail("studio.html: data block missing or duplicated")
    if "\"workflows\":[]" in html:
        fail("studio.html was built with no workflows")
    print("   no external requests; data block present")


def main() -> int:
    step("validate", [PY, str(ROOT / "tools" / "validate.py")])
    step("build", [PY, str(ROOT / "tools" / "build.py")])
    step("docs", [PY, str(ROOT / "tools" / "docs.py")])
    check_studio_html()
    step("orchestrate check", [PY, str(FW_TOOLS / "orchestrate.py"), "check"])

    with tempfile.TemporaryDirectory(prefix="workflow-studio-fixture-") as tmp:
        root = Path(tmp)
        fixture(root)
        step("fixture: logic_index", [PY, str(FW_TOOLS / "logic_index.py")], cwd=root)
        step("fixture: components_index", [PY, str(FW_TOOLS / "components_index.py")], cwd=root)
        step("fixture: decisions_index", [PY, str(FW_TOOLS / "decisions_index.py")], cwd=root)
        idx = (root / "logic" / "INDEX.md").read_text(encoding="utf-8")
        if "`login`" not in idx or "`reset-password`" not in idx or "finding" in idx:
            fail("fixture: logic/INDEX.md does not list the two nodes cleanly")
        comps = (root / "code" / "COMPONENTS.md").read_text(encoding="utf-8")
        if "`auth` → `login`, `reset-password`" not in comps or "finding" in comps:
            fail("fixture: code/COMPONENTS.md does not map auth → login, reset-password cleanly")
        step("fixture: install_commands --agent all", [PY, str(FW_TOOLS / "install_commands.py"), "--agent", "all"], cwd=root)
        first = sorted(p.relative_to(root) for p in root.glob(".*/**/*") if p.is_file())
        step("fixture: install_commands again (idempotent)", [PY, str(FW_TOOLS / "install_commands.py"), "--agent", "all"], cwd=root)
        second = sorted(p.relative_to(root) for p in root.glob(".*/**/*") if p.is_file())
        if first != second or not any(str(p).startswith(".claude/skills/speckit-") for p in first):
            fail("fixture: installer output is not idempotent or not in the Spec Kit skills layout")
        # a broken decision log must be refused
        (root / "decisions" / "D-0002-bad.md").write_text(
            GOOD_DECISION.replace('"2026-09-09T14:32+05:30"', '"2026-09-09"').replace("nodes: [login]", "supersedes: D-0099"),
            encoding="utf-8")
        step("fixture: decisions_index refuses a broken log", [PY, str(FW_TOOLS / "decisions_index.py")], cwd=root, expect=1)
        runner_fixture(root)
        group_fixture(root)

    # new_product.py: one-command bootstrap must produce a CLOSED product folder and refuse a non-empty one
    with tempfile.TemporaryDirectory(prefix="workflow-studio-newproduct-") as tmp:
        dest = Path(tmp) / "p"
        step("new_product: bootstrap", [PY, str(ROOT / "tools" / "new_product.py"), str(dest), "--agent", "claude", "--no-git", "--run", "python3 -m app", "--test", "python3 -m pytest"])
        for must in ("framework/tools/orchestrate.py", "framework/workflows/define.yaml", "AGENTS.md", "CLAUDE.md", "architecture.md", "changes/QUEUE.md", ".claude/skills/speckit-specify/SKILL.md"):
            if not (dest / must).exists():
                fail(f"new_product: {must} missing")
        if "python3 -m pytest" not in (dest / "AGENTS.md").read_text(encoding="utf-8"):
            fail("new_product: AGENTS.md placeholders not filled")
        step("new_product: refuses a non-empty folder", [PY, str(ROOT / "tools" / "new_product.py"), str(dest), "--agent", "claude"], expect=1)

    # optional: archify_delta refuses cleanly when the CLI is absent, and works when present
    ad = FW_TOOLS / "archify_delta.py"
    r = subprocess.run([PY, str(ad), "locate"], capture_output=True, text=True)
    if r.returncode == 0:
        with tempfile.TemporaryDirectory(prefix="workflow-studio-archify-") as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            base = {"schema_version": 1, "diagram_type": "architecture", "meta": {"title": "a"},
                    "components": [{"id": "x", "type": "backend", "label": "X", "pos": [40, 40], "size": [120, 60]},
                                   {"id": "y", "type": "database", "label": "Y", "pos": [240, 40], "size": [120, 60]}],
                    "boundaries": [], "connections": [{"id": "xy", "from": "x", "to": "y"}]}
            head = json.loads(json.dumps(base)); head["connections"] = []
            (root / "before.json").write_text(json.dumps(base), encoding="utf-8")
            (root / "docs" / "architecture.archify.json").write_text(json.dumps(head), encoding="utf-8")
            step("optional: archify_delta compare reports a removal", [PY, str(ad), "compare", "before.json"], cwd=root, expect=2)
    else:
        print("== optional: archify_delta (skipped: archify CLI not installed on this machine)")
        step("optional: archify_delta refuses without the CLI", [PY, str(ad), "locate"], expect=1)

    print("\nALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
