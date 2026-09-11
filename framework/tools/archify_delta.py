#!/usr/bin/env python3
"""Render the product's architecture diagram and its before/after Delta with archify.

Optional output of the framework (framework/components/architecture-file.md,
"Optional diagram"). Enabled when the architecture file names archify among the
tools; never a gate input.

Usage, from the product repository root:
  python3 framework/tools/archify_delta.py locate
      Print the archify CLI path, or exit 1 with the install command.
  python3 framework/tools/archify_delta.py install
      Install the archify skill for the tools on this machine (runs
      `npx skills add tt-a1i/archify -g`; needs Node.js 18+ and the network).
  python3 framework/tools/archify_delta.py render [--json docs/architecture.archify.json]
      Validate and render docs/architecture.html from the JSON.
  python3 framework/tools/archify_delta.py compare <before.json> [--json docs/architecture.archify.json]
      Validate both files, write docs/architecture.delta.html and
      docs/architecture.delta.json (the receipt), then print every component
      and connection the receipt marks removed. Exit 2 when removals exist,
      so deliver.challenge-plan can require each one to be named in the plan.

The archify CLI is looked up at ARCHIFY_CLI, then in the skill folders
~/.agents/skills/archify, ~/.claude/skills/archify, ~/.config/opencode/skills/archify.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()
DEFAULT_JSON = ROOT / "docs" / "architecture.archify.json"
CANDIDATES = [
    Path.home() / ".agents" / "skills" / "archify" / "bin" / "archify.mjs",
    Path.home() / ".claude" / "skills" / "archify" / "bin" / "archify.mjs",
    Path.home() / ".config" / "opencode" / "skills" / "archify" / "bin" / "archify.mjs",
]
INSTALL_HINT = "install with: python3 framework/tools/archify_delta.py install   (or: npx skills add tt-a1i/archify -g)"


def refuse(msg: str, code: int = 1) -> int:
    print(f"refused: {msg}")
    return code


def locate() -> Path | None:
    env = os.environ.get("ARCHIFY_CLI")
    if env and Path(env).is_file():
        return Path(env)
    for c in CANDIDATES:
        if c.is_file():
            return c
    return None


def node() -> str | None:
    return shutil.which("node")


def run(cli: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([node() or "node", str(cli), *args], capture_output=True, text=True)


def cmd_locate(_a) -> int:
    cli = locate()
    if not cli:
        return refuse(f"archify CLI not found; {INSTALL_HINT}")
    if not node():
        return refuse("node is not on PATH; archify needs Node.js 18 or later")
    print(cli)
    return 0


def cmd_install(_a) -> int:
    if not shutil.which("npx"):
        return refuse("npx is not on PATH; install Node.js 18 or later first")
    r = subprocess.run(["npx", "skills", "add", "tt-a1i/archify", "-g"], text=True)
    if r.returncode != 0:
        return refuse(f"npx skills add exited {r.returncode}")
    cli = locate()
    if not cli:
        return refuse("install finished but no archify.mjs was found in the known skill folders; set ARCHIFY_CLI")
    print(f"installed: {cli}")
    return 0


def need(a, path: Path) -> int | None:
    if not path.is_file():
        return refuse(f"{path.relative_to(ROOT) if path.is_relative_to(ROOT) else path} does not exist")
    return None


def cmd_render(a) -> int:
    cli = locate()
    if not cli:
        return refuse(f"archify CLI not found; {INSTALL_HINT}")
    src = Path(a.json)
    if (e := need(a, src)) is not None:
        return e
    out = ROOT / "docs" / "architecture.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    v = run(cli, "validate", "architecture", str(src))
    if v.returncode != 0:
        print(v.stdout, v.stderr, sep="")
        return refuse(f"{src.name} does not validate")
    r = run(cli, "render", "architecture", str(src), str(out))
    if r.returncode != 0:
        print(r.stdout, r.stderr, sep="")
        return refuse("render failed")
    print(f"rendered {out.relative_to(ROOT)}")
    return 0


def cmd_compare(a) -> int:
    cli = locate()
    if not cli:
        return refuse(f"archify CLI not found; {INSTALL_HINT}")
    before, after = Path(a.before), Path(a.json)
    for p in (before, after):
        if (e := need(a, p)) is not None:
            return e
    docs = ROOT / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    html, receipt = docs / "architecture.delta.html", docs / "architecture.delta.json"
    for p in (before, after):
        v = run(cli, "validate", "architecture", str(p))
        if v.returncode != 0:
            print(v.stdout, v.stderr, sep="")
            return refuse(f"{p.name} does not validate")
    r = run(cli, "compare", "architecture", str(before), str(after), str(html), "--receipt", str(receipt))
    if r.returncode != 0 or not receipt.is_file():
        print(r.stdout, r.stderr, sep="")
        return refuse("compare failed")
    data = json.loads(receipt.read_text(encoding="utf-8"))
    s = data.get("summary", {})
    comp, conn, bnd = s.get("components", {}), s.get("connections", {}), s.get("boundaries", {})
    print(f"delta: components +{comp.get('added', 0)} ~{comp.get('changed', 0)} -{comp.get('removed', 0)}; "
          f"connections +{conn.get('added', 0)} ~{conn.get('changed', 0)} -{conn.get('removed', 0)}; "
          f"boundaries ~{bnd.get('changed', 0)}")
    print(f"wrote {html.relative_to(ROOT)} and {receipt.relative_to(ROOT)}")
    removed = []
    ch = data.get("changes", {})
    for c in ch.get("components", []):
        if c.get("status") == "removed":
            removed.append(f"component {c.get('id')} ({(c.get('base') or {}).get('label', c.get('baseLabel', ''))})")
    for c in ch.get("connections", []):
        if c.get("status") == "removed":
            b = c.get("base") or {}
            removed.append(f"connection {c.get('id')} ({b.get('from')} → {b.get('to')}, {b.get('label', '')})")
    if removed:
        print("removed, must be named in the plan section or restored:")
        for r_ in removed:
            print(f"  - {r_}")
        return 2
    print("no removals")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("locate")
    sub.add_parser("install")
    r = sub.add_parser("render"); r.add_argument("--json", default=str(DEFAULT_JSON))
    c = sub.add_parser("compare"); c.add_argument("before"); c.add_argument("--json", default=str(DEFAULT_JSON))
    a = ap.parse_args()
    return {"locate": cmd_locate, "install": cmd_install, "render": cmd_render, "compare": cmd_compare}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
