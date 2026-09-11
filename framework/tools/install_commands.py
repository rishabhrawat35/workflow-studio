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
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path.cwd()
SRC = ROOT / "framework" / "commands"
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", required=True, choices=list(SKILL_DIRS) + ["gemini", "all"])
    ap.add_argument("--with-archify", action="store_true", help="also install the archify diagram skill (npx skills add tt-a1i/archify -g)")
    a = ap.parse_args()
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
        import subprocess
        r = subprocess.run([sys.executable, str(Path(__file__).with_name("archify_delta.py")), "install"])
        return r.returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
