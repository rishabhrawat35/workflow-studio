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
Stdlib only (plus PyYAML, which every tool here already needs).
"""
import re
import shutil
import json
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
