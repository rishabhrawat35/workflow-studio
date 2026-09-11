#!/usr/bin/env python3
"""Create a product repository that runs this framework, in one command.

Usage, from anywhere:
  python3 <workflow-studio>/tools/new_product.py <folder> --agent claude|codex|copilot|gemini|cursor|all
      [--run "<command that runs the product>"] [--test "<whole test suite command>"]
      [--with-archify] [--with-ecc] [--no-git]

What it does, in order:
  1. Creates <folder> (refuses a non-empty folder) and runs `git init` unless --no-git.
  2. Copies framework/ and workflows/ (into framework/workflows/), AGENTS.md and CLAUDE.md
     from the templates, and fills the two command placeholders with --run and --test.
  3. Writes a starter architecture.md the PM completes at the first foundation step.
  4. Installs the slash commands for --agent (install_commands.py), and the optional
     archify diagram skill (--with-archify) and ECC toolbox (--with-ecc).
  5. Runs `orchestrate.py check`, which must print CLOSED, and prints the first command to type.

Spec Kit is not installed and not needed: the framework only reuses its command names.
"""
from __future__ import annotations
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

STUDIO = Path(__file__).resolve().parent.parent
AGENTS = ["claude", "codex", "copilot", "gemini", "cursor", "all"]
ARCH = """# Architecture

Written by the PM; the AI never generates it. Complete it at the first
foundation step (`/speckit-constitution`) or now. Every line below is a rule
the AI builds within; an unwritten rule is never checked.

## Tools, language and resources
- Language and version: <e.g. Python 3.9>
- Test runner and how the whole suite runs: <e.g. pytest; python3 -m pytest>
- Optional toolboxes named here are used by the runner: archify (architecture diagrams), ECC (reviewers at verify)

## Systems and layout
- Systems: <e.g. backend>; components live in code/<system>/<component>/ with tests beside the code

## Rules
- Security, accessibility, performance: <rules the AI must check>

## Running the product
- <command>

## Environments, variables and secrets
- Where environment values and secrets live and how the PM supplies them: <never in logic files or change records>

## Never
- <things the AI must never do in this product>
"""


def sh(argv, cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    r = subprocess.run(argv, cwd=str(cwd), capture_output=True, text=True)
    if check and r.returncode != 0:
        print(r.stdout, r.stderr, sep="")
        print(f"refused: `{' '.join(argv)}` exited {r.returncode}")
        sys.exit(1)
    return r


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("folder")
    ap.add_argument("--agent", required=True, choices=AGENTS)
    ap.add_argument("--run", default="<from architecture.md>")
    ap.add_argument("--test", default="<exact command>")
    ap.add_argument("--with-archify", action="store_true")
    ap.add_argument("--with-ecc", action="store_true")
    ap.add_argument("--no-git", action="store_true")
    a = ap.parse_args()

    dest = Path(a.folder).expanduser().resolve()
    if dest.exists() and any(dest.iterdir()):
        print(f"refused: {dest} exists and is not empty")
        return 1
    for need in ("framework", "workflows", "framework/templates/AGENTS.md", "framework/templates/CLAUDE.md"):
        if not (STUDIO / need).exists():
            print(f"refused: {STUDIO / need} is missing; run this from a complete workflow-studio checkout")
            return 1

    dest.mkdir(parents=True, exist_ok=True)
    shutil.copytree(STUDIO / "framework", dest / "framework", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copytree(STUDIO / "workflows", dest / "framework" / "workflows")
    for name in ("AGENTS.md", "CLAUDE.md"):
        text = (STUDIO / "framework" / "templates" / name).read_text(encoding="utf-8")
        text = text.replace("<from architecture.md>", a.run).replace("<exact command>", a.test)
        (dest / name).write_text(text, encoding="utf-8")
    (dest / "architecture.md").write_text(ARCH.replace("<e.g. pytest; python3 -m pytest>", a.test if a.test != "<exact command>" else "<e.g. pytest; python3 -m pytest>").replace("- <command>", f"- {a.run}"), encoding="utf-8")
    (dest / "changes").mkdir()
    (dest / "changes" / "QUEUE.md").write_text("# Queue\n\nNo records yet.\n", encoding="utf-8")
    (dest / ".gitignore").write_text("__pycache__/\n*.pyc\nchanges/runs/\n", encoding="utf-8")
    print(f"created {dest} with framework/, framework/workflows/, AGENTS.md, CLAUDE.md, architecture.md, changes/")

    if not a.no_git:
        if shutil.which("git"):
            sh(["git", "init", "-q"], dest)
            print("git: initialised")
        else:
            print("git: not on PATH; skipped (install git before the first commit)")

    argv = [sys.executable, "framework/tools/install_commands.py", "--agent", a.agent]
    if a.with_ecc:
        argv.append("--with-ecc")
    r = sh(argv, dest, check=False)
    print(r.stdout.rstrip())
    if r.returncode != 0:
        print(r.stderr.rstrip())
        print("refused: slash-command install failed (see above)")
        return 1
    if a.with_archify:
        r = sh([sys.executable, "framework/tools/archify_delta.py", "install"], dest, check=False)
        print(r.stdout.rstrip() or r.stderr.rstrip())
        if r.returncode != 0:
            print("archify: install failed; the option stays off until `framework/tools/archify_delta.py install` succeeds")

    r = sh([sys.executable, "framework/tools/orchestrate.py", "check"], dest, check=False)
    print(r.stdout.rstrip())
    if r.returncode != 0 or "CLOSED" not in r.stdout:
        print("refused: orchestrate.py check is not CLOSED in the new folder")
        return 1

    prefix = "/speckit." if a.agent == "gemini" else "/speckit-"
    print("\nNext:")
    print(f"  1. Complete architecture.md (or answer {prefix}constitution in your AI tool).")
    print(f"  2. Open your AI tool in {dest} and type: {prefix}specify <what the product should do, in your words>")
    print(f"  3. Or from a terminal: python3 framework/tools/orchestrate.py start changes/<date>-1-<slug>.md --command speckit.specify")
    return 0


if __name__ == "__main__":
    sys.exit(main())
