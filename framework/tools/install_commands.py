#!/usr/bin/env python3
"""Install the framework's slash commands into a product repository for one AI tool.

Usage (from the product repository root, with framework/ copied in):
  python3 framework/tools/install_commands.py --agent claude|codex|copilot|gemini|cursor|all

Layout mirrors GitHub Spec Kit >= 1.0 (skills, invoked as /speckit-<name>), so a
later move either way is a file swap:
  claude   .claude/skills/speckit-<name>/SKILL.md
  codex    .agents/skills/speckit-<name>/SKILL.md
  copilot  .github/skills/speckit-<name>/SKILL.md
  cursor   .cursor/skills/speckit-<name>/SKILL.md
  gemini   .gemini/commands/speckit.<name>.toml   (description + prompt, {{args}})
Templates live in framework/commands/speckit.<name>.md with `$ARGUMENTS` as the
argument placeholder; the installer rewrites it per tool.
`--with-archify` also installs the optional archify diagram skill (see
framework/tools/archify_delta.py).
`--with-ecc` also installs ECC (github.com/affaan-m/ECC), the optional toolbox
framework/orchestration/toolbox.yaml names: non-interactively, profile minimal,
target claude, hooks off (`npx ecc-universal@2.2.1 install --profile minimal
--target claude --yes --no-hooks`; falls back to `git clone` + `./install.sh
--profile minimal --target claude` when npx is missing). Afterwards it verifies
that no ECC hook is registered in ~/.claude/settings.json and exits 1 with the
instruction if one is. Hooks are never installed by the framework: a hook runs
outside the record and the orchestrator, so nothing it does is gated.
"""
from __future__ import annotations
import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path.cwd()
SRC = ROOT / "framework" / "commands"
ECC_VERSION = "2.2.1"
ECC_REPO = "https://github.com/affaan-m/ECC"
ECC_NPX = ["npx", "--yes", f"ecc-universal@{ECC_VERSION}", "install", "--profile", "minimal", "--target", "claude", "--yes", "--no-hooks"]
ECC_SH = ["./install.sh", "--profile", "minimal", "--target", "claude"]
SKILL_DIRS = {"claude": ".claude/skills", "codex": ".agents/skills", "copilot": ".github/skills", "cursor": ".cursor/skills"}
FM = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.S)


def split(text):
    m = FM.match(text)
    if not m:
        return {}, text
    meta = dict(l.split(":", 1) for l in m.group(1).splitlines() if ":" in l)
    return {k.strip(): v.strip() for k, v in meta.items()}, m.group(2)


def skill_md(name, meta, body, args_token):
    desc = meta.get("description", name).replace("\\", "\\\\").replace('"', '\\"')  # a YAML double-quoted string: escape, do not alter
    return f"---\nname: {name.replace('.', '-')}\ndescription: \"{desc}\"\n---\n" + body.replace("$ARGUMENTS", args_token)


def toml(name, meta, body):
    # basic strings: a backslash is an escape, so it must be doubled or the file is invalid TOML
    desc = meta.get("description", name).replace("\\", "\\\\").replace('"', '\\"')  # TOML basic strings: escape, do not alter
    b = body.replace("$ARGUMENTS", "{{args}}").replace("\\", "\\\\").replace('"""', '""\\"')
    return f'description = "{desc}"\nprompt = """\n{b}\n"""\n'


def ecc_hooks_registered(settings: Path) -> list[str]:
    """Every hook command under ~/.claude/settings.json that points at ECC (its hooks folder or its name)."""
    if not settings.exists():
        return []
    try:
        data = json.loads(settings.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return [f"{settings}: cannot be read as JSON ({e}); check it by hand"]
    found = []
    hooks = data.get("hooks") if isinstance(data, dict) else None
    if not isinstance(hooks, dict):
        return found
    for event, entries in hooks.items():
        for entry in entries if isinstance(entries, list) else []:
            for h in (entry.get("hooks") if isinstance(entry, dict) else None) or []:
                cmd = str((h or {}).get("command", ""))
                if "ecc" in cmd.lower() or "/.claude/hooks/" in cmd:
                    found.append(f"{event}: {cmd}")
    return found


def install_ecc() -> int:
    """Non-interactive ECC install: npx path first, git clone + install.sh as the fallback; then the hook check."""
    if shutil.which("npx"):
        print("ecc: " + " ".join(ECC_NPX))
        r = subprocess.run(ECC_NPX)
        ok = r.returncode == 0
    else:
        ok = False
        print("ecc: npx not on PATH; trying git clone + install.sh")
    if not ok:
        if not shutil.which("git"):
            print("ecc: neither npx nor git is available; install Node.js 18+ or git and run again")
            return 1
        with tempfile.TemporaryDirectory(prefix="ecc-") as tmp:
            r = subprocess.run(["git", "clone", "--depth", "1", ECC_REPO, tmp])
            if r.returncode != 0:
                print("ecc: git clone failed (network?); nothing installed")
                return 1
            print("ecc: " + " ".join(ECC_SH))
            r = subprocess.run(ECC_SH, cwd=tmp)
            if r.returncode != 0:
                print("ecc: install.sh failed; nothing verified")
                return 1
    settings = Path.home() / ".claude" / "settings.json"
    hooks = ecc_hooks_registered(settings)
    if hooks:
        print(f"ecc: hooks are registered in {settings}; the framework never runs hooks (nothing a hook does is gated by the record):")
        for h in hooks:
            print("  -", h)
        print("remove them: `npx ecc-universal@" + ECC_VERSION + " uninstall --target claude` then reinstall with --no-hooks, or delete the entries above from the `hooks` key by hand")
        return 1
    print(f"ecc: installed (profile minimal, target claude, no hooks); no ECC hook in {settings}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", required=True, choices=list(SKILL_DIRS) + ["gemini", "all"])
    ap.add_argument("--with-archify", action="store_true", help="also install the archify diagram skill (npx skills add tt-a1i/archify -g)")
    ap.add_argument("--with-ecc", action="store_true", help="also install ECC non-interactively (profile minimal, target claude, hooks off) and verify no hook is registered")
    ap.add_argument("--check-ecc-hooks", action="store_true", help="only run the hook check against ~/.claude/settings.json")
    a = ap.parse_args()
    if a.check_ecc_hooks:
        hooks = ecc_hooks_registered(Path.home() / ".claude" / "settings.json")
        for h in hooks:
            print("  -", h)
        print("ecc hooks: " + ("REGISTERED, remove them" if hooks else "none registered"))
        return 1 if hooks else 0
    if not SRC.exists():
        print("framework/commands not found; run from the product repository root")
        return 1
    agents = list(SKILL_DIRS) + ["gemini"] if a.agent == "all" else [a.agent]
    n = 0
    for ag in agents:
        for f in sorted(SRC.glob("speckit.*.md")):
            meta, body = split(f.read_text(encoding="utf-8"))
            name = f.stem
            if ag == "gemini":
                out = ROOT / ".gemini" / "commands" / f"{name}.toml"
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(toml(name, meta, body), encoding="utf-8")
            else:
                out = ROOT / SKILL_DIRS[ag] / name.replace(".", "-") / "SKILL.md"
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(skill_md(name, meta, body, "$ARGUMENTS"), encoding="utf-8")
            n += 1
        print(f"{ag}: {SKILL_DIRS.get(ag, '.gemini/commands')}/")
    print(f"installed {n} file(s); invoke as /speckit-<name> (Gemini: /speckit.<name>)")
    if a.with_archify:
        r = subprocess.run([sys.executable, str(Path(__file__).with_name("archify_delta.py")), "install"])
        if r.returncode != 0:
            return r.returncode
    if a.with_ecc:
        return install_ecc()
    return 0


if __name__ == "__main__":
    sys.exit(main())
