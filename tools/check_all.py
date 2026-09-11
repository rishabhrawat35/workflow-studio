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
    for pm_step, answer in stops:
        step(f"runner: run to the PM stop {pm_step} (exit 3)", fake, cwd=root, expect=3)
        text = (root / rec).read_text(encoding="utf-8")
        if f"step: {pm_step}" not in text:
            fail(f"runner: the record is not at {pm_step}")
        step(f"runner: PM answers at {pm_step}", [PY, orch, "advance", rec] + answer, cwd=root)
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
