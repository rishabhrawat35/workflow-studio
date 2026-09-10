#!/usr/bin/env python3
"""Generate framework/steps.md from workflows/*.yaml and map.yaml.

Every step gets: what it is, who owns it, what comes in (previous steps and
incoming handoffs), what goes out (next steps with conditions), and notes.
Nothing here is written by hand; edit the YAML and rerun.
"""
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "framework" / "steps.md"


def targets(step):
    out = []
    for t in step.get("next") or []:
        out.append((t, None) if isinstance(t, str) else (t["to"], t.get("when")))
    return out


def main() -> int:
    # the generator assumes valid files; refuse (instead of crashing) on anything the validator rejects
    v = subprocess.run([sys.executable, str(ROOT / "tools" / "validate.py")], capture_output=True, text=True)
    if v.returncode != 0:
        print(v.stdout.rstrip())
        print("docs aborted: validation failed")
        return 1
    wfs = {}
    for p in sorted((ROOT / "workflows").glob("*.yaml")):
        d = yaml.safe_load(p.read_text(encoding="utf-8"))
        wfs[d["id"]] = d
    mp = yaml.safe_load((ROOT / "map.yaml").read_text(encoding="utf-8")) or {}
    groups = mp.get("groups") or []

    # incoming edges: (workflow, step) -> [(from_workflow, from_step, condition, is_handoff)]
    incoming = {}
    for wid, w in wfs.items():
        for s in w["steps"]:
            for to, when in targets(s):
                incoming.setdefault((wid, to), []).append((wid, s["id"], when, False))
            if s.get("type") == "handoff":
                tw, ts = s["to"].split(".")
                incoming.setdefault((tw, ts), []).append((wid, s["id"], None, True))

    def title(wid, sid):
        return next(x["title"] for x in wfs[wid]["steps"] if x["id"] == sid)

    lines = [
        "# Step reference",
        "",
        "Generated from `workflows/*.yaml` and `map.yaml` by `tools/docs.py`. Do not edit by hand.",
        "",
        "Step ids are written `workflow.step`. Owner is the workflow owner unless a step says otherwise.",
        "",
        f"**System entry:** `{mp.get('entry')}` — where the PM's input enters. **System exit:** `{mp.get('exit')}` — where the finished result leaves.",
        "",
    ]
    for g in groups:
        for wid in g["workflows"]:
            w = wfs[wid]
            lines += [
                f"## {w['name']}  (`{wid}`, group: {g['name']})",
                "",
                f"**Owner:** {w['owner']}  ",
                f"**Purpose:** {w['purpose'].strip()}  ",
                f"**Starts when:** {w['trigger'].strip()}  ",
                f"**Entry step:** `{wid}.{w['steps'][0]['id']}`",
                "",
            ]
            for s in w["steps"]:
                owner = s.get("owner", w["owner"])
                labels = []
                if s is w["steps"][0]:
                    labels.append("ENTRY")
                if s.get("type") in ("end", "handoff"):
                    labels.append("EXIT")
                if "input" in s:
                    labels.append("PM INPUT")
                lines += [f"### `{wid}.{s['id']}` — {s['title']}", "", f"Type: {s['type']}. Owner: {owner}." + (f" Labels: {', '.join(labels)}." if labels else ""), ""]
                if s.get("input"):
                    lines += [f"PM provides: {s['input'].strip()}", ""]
                if s.get("output"):
                    lines += [f"Produces: {s['output'].strip()}", ""]
                if s.get("what"):
                    lines += [s["what"].strip(), ""]
                if s.get("notes"):
                    lines += [f"Notes: {s['notes'].strip()}", ""]
                inc = incoming.get((wid, s["id"]), [])
                if inc:
                    lines.append("Comes from:")
                    for fw, fs, when, hand in inc:
                        via = " (handoff from another workflow)" if hand else (f" — when {when}" if when else "")
                        lines.append(f"- `{fw}.{fs}` {title(fw, fs)}{via}")
                    lines.append("")
                elif s is w["steps"][0]:
                    lines += ["Comes from: the workflow trigger.", ""]
                outs = targets(s)
                if s.get("type") == "handoff":
                    tw, ts = s["to"].split(".")
                    lines += [f"Hands off to: `{s['to']}` {title(tw, ts)} in *{wfs[tw]['name']}*.", ""]
                if outs:
                    lines.append("Goes to:")
                    for to, when in outs:
                        lines.append(f"- `{wid}.{to}` {title(wid, to)}" + (f" — when {when}" if when else ""))
                    lines.append("")
                if s.get("type") == "end":
                    lines += ["Goes to: nothing; the workflow ends here.", ""]
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({sum(len(w['steps']) for w in wfs.values())} steps)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
