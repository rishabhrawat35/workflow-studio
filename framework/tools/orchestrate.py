#!/usr/bin/env python3
"""Orchestration layer 1 for a product built with the framework.

The workflow YAML is the state machine; a change record's front matter is
its state; this tool is the only thing that moves state. An AI runs a
step; it never decides the next step by itself, and it cannot move past a
gate or a challenge without the artefact that gate or challenge produces.

Usage (from the product repository root, with framework/ copied in):
  orchestrate.py check
      prove the system is closed (run before anything else)
  orchestrate.py start <record.md> --command speckit.<name> [--lane small|full]
      create a record at an ENTRY command's step (define.intake). Every other
      command is a `next` on a record already at that step; `start` refuses it.
  orchestrate.py next <record.md> [--json]
      what happens now: step, mode, role, inputs, framing, legal exits, last edges;
      --json prints the same as one JSON object for the runner (framework/tools/run.py)
  orchestrate.py advance <record.md> --to <step|bare step id|index|prefix> [--when "<condition|index>"]
                        [--answer "<PM's answer>"] [--lane small|full]
      move the record along one edge. Refuses: an exit not in the YAML; a
      decision without its condition; a mismatched condition; leaving a PM
      step without --answer; leaving a challenger step without a findings
      block for that step, or with zero findings while a rerun framing is
      still unused (full lane); a fourth execute after three failed passes;
      --lane anywhere but at start or leaving define.sort; any exit from a
      handoff other than its `to:` target.
  orchestrate.py rerun <record.md>
      a challenger found nothing on non-trivial work: pick the next framing

Findings block: the AI writes `## Findings — <step>` into the record body
before leaving a challenger step; a body line "none" under it means zero
findings. PM answers are recorded from --answer into history.
Exit code 1 on any refusal, so a wrapper can stop.

A command in commands.yaml may carry `meta: true` with `enters: current`: it
wraps the runner and enters whatever step the record is at (speckit.run);
`start` refuses it and `check` exempts it from the enters rule only.
`framework/orchestration/toolbox.yaml`, when present, is validated by `check`:
every key under `steps` must be a real step.
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path.cwd()
FW = ROOT / "framework"
WF_DIR = FW / "workflows" if (FW / "workflows").exists() else ROOT / "workflows"
ORCH = FW / "orchestration"
FM = re.compile(r"^---\s*\n(.*?)\n---\s*(?:\n(.*))?$", re.S)
ENTRY_STEPS = {"define.intake"}
MAX_FAILED = 3


class Refused(Exception):
    """A refusal: printed as `refused: …`, exit 1."""


def load_yaml(p: Path):
    with p.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_system():
    workflows = {}
    if not list(WF_DIR.glob("*.yaml")):
        raise Refused(f"no workflow files in {WF_DIR.relative_to(ROOT) if WF_DIR.is_relative_to(ROOT) else WF_DIR}/; from the workflow-studio checkout run "
                      "`cp -r /path/to/workflow-studio/workflows framework/` so they sit in framework/workflows/")
    for p in sorted(WF_DIR.glob("*.yaml")):
        d = load_yaml(p)
        workflows[d["id"]] = d
    roles = load_yaml(ORCH / "roles.yaml")
    commands = load_yaml(ORCH / "commands.yaml")["commands"]
    return workflows, roles, commands


def load_toolbox():
    """framework/orchestration/toolbox.yaml, or None when the product has none."""
    p = ORCH / "toolbox.yaml"
    return load_yaml(p) if p.exists() else None


def check_toolbox(workflows, toolbox) -> list[str]:
    problems = []
    if toolbox is None:
        return problems
    all_steps = {f"{wid}.{s['id']}" for wid, w in workflows.items() for s in w["steps"]}
    if not isinstance(toolbox.get("enabled_when"), str) or not toolbox["enabled_when"].strip():
        problems.append("toolbox.yaml: `enabled_when` must be a non-empty string searched in architecture.md")
    if not isinstance(toolbox.get("never"), list):
        problems.append("toolbox.yaml: `never` must be a list")
    steps = toolbox.get("steps") or {}
    if not isinstance(steps, dict):
        problems.append("toolbox.yaml: `steps` must be a mapping of step → {use, note, passes}")
        return problems
    for ref, row in steps.items():
        if ref not in all_steps:
            problems.append(f"toolbox.yaml: unknown step {ref}")
        if not isinstance(row, dict) or not isinstance(row.get("use"), list) or not row["use"]:
            problems.append(f"toolbox.yaml: {ref} needs a non-empty `use` list")
    return problems


def step_of(workflows, ref):
    wid, _, sid = ref.partition(".")
    w = workflows.get(wid)
    if not w:
        return None, None
    return w, next((s for s in w["steps"] if s["id"] == sid), None)


def norm(s):
    return re.sub(r"\s+", " ", str(s or "")).strip().casefold()


def exits(workflows, ref):
    """Legal exits: [(target_ref, when)]. A handoff's only exit is its `to:`;
    its local `next` (the drawing's end) is recorded as a closure, not taken."""
    w, s = step_of(workflows, ref)
    if s.get("type") == "handoff":
        return [(s["to"], "handoff")]
    out = []
    for t in s.get("next") or []:
        out.append((f"{w['id']}.{t}", None) if isinstance(t, str) else (f"{w['id']}.{t['to']}", t.get("when")))
    return out


def local_closure(workflows, ref):
    w, s = step_of(workflows, ref)
    if s.get("type") == "handoff":
        nxt = s.get("next") or []
        return f"{w['id']}.{nxt[0]}" if nxt else None
    return None


# ---------------------------------------------------------------- check
def check(workflows, roles, commands) -> list[str]:
    problems = []
    all_steps = {f"{wid}.{s['id']}" for wid, w in workflows.items() for s in w["steps"]}
    mapped = set(roles["steps"])
    for ref in sorted(all_steps - mapped):
        problems.append(f"roles.yaml: step {ref} has no role/mode mapping")
    for ref in sorted(mapped - all_steps):
        problems.append(f"roles.yaml: maps unknown step {ref}")
    for ref, cfg in roles["steps"].items():
        if ref not in all_steps:
            continue
        w, s = step_of(workflows, ref)
        owner = s.get("owner", w["owner"])
        t = s.get("type")
        if cfg["mode"] == "pm" and owner != "PM":
            problems.append(f"roles.yaml: {ref} is mode pm but the step is owned by {owner}")
        if cfg["mode"] != "pm" and "input" in s:
            problems.append(f"roles.yaml: {ref} takes PM input but mode is {cfg['mode']}")
        if cfg["mode"] == "pm" and "input" not in s:
            problems.append(f"roles.yaml: {ref} is mode pm but the step has no `input`")
        if cfg["mode"] == "challenger" and not cfg.get("framings"):
            problems.append(f"roles.yaml: challenger step {ref} has no framings")
        if cfg["mode"] == "auto" and t not in ("handoff", "end"):
            problems.append(f"roles.yaml: {ref} is mode auto but is a {t}; auto is only for handoffs and ends (routing without judgment)")
        if t in ("handoff", "end") and cfg["mode"] != "auto":
            problems.append(f"roles.yaml: {ref} is a {t} and must be mode auto")
        if cfg.get("role") not in roles["roles"]:
            problems.append(f"roles.yaml: {ref} names unknown role {cfg.get('role')}")
    for name, c in commands.items():
        if c.get("meta"):
            if c.get("enters") != "current" or c.get("entry"):
                problems.append(f"commands.yaml: {name} is meta and must have `enters: current` and no `entry`")
            if not name.startswith("speckit."):
                problems.append(f"commands.yaml: {name} must carry the speckit. prefix")
            continue
        if "enters" not in c:
            problems.append(f"commands.yaml: {name} has no `enters` step")
            continue
        if c["enters"] not in all_steps:
            problems.append(f"commands.yaml: {name} enters unknown step {c['enters']}")
        elif roles["steps"].get(c["enters"], {}).get("mode") == "auto":
            problems.append(f"commands.yaml: {name} enters {c['enters']}, a routing-only step")
        if c.get("entry") and c["enters"] not in ENTRY_STEPS:
            problems.append(f"commands.yaml: {name} is marked entry but enters {c['enters']}")
        if not name.startswith("speckit."):
            problems.append(f"commands.yaml: {name} must carry the speckit. prefix")
    for ref in all_steps:
        w, s = step_of(workflows, ref)
        ex = exits(workflows, ref)
        seen = set()
        for tgt, when in ex:
            if tgt not in all_steps:
                problems.append(f"{ref}: exit to unknown step {tgt}")
            if s.get("type") == "decision" and len(ex) > 1 and not when:
                problems.append(f"{ref}: a decision exit without a condition")
            if when and norm(when) in seen:
                problems.append(f"{ref}: two exits share the condition '{when}'")
            seen.add(norm(when))
    return problems


# ---------------------------------------------------------------- records
def read_record(path: Path):
    if not path.exists():
        raise Refused(f"no record at {path}")
    text = path.read_text(encoding="utf-8")
    m = FM.match(text)
    if not m:
        return {}, text
    meta = yaml.safe_load(m.group(1)) or {}
    if not isinstance(meta, dict):
        raise Refused("record front matter must be a mapping")
    for k in ("failed_passes", "rerun_count"):
        if k in meta and not (isinstance(meta[k], int) and not isinstance(meta[k], bool)):
            raise Refused(f"record field `{k}` must be an integer, not {meta[k]!r}")
    if "history" in meta and (not isinstance(meta["history"], list) or not all(isinstance(h, dict) for h in meta["history"])):
        raise Refused("record field `history` must be a list of edges (mappings)")
    return meta, (m.group(2) or "")


def write_record(path: Path, meta: dict, body: str):
    fm = yaml.safe_dump(meta, sort_keys=False, allow_unicode=True, width=1000).strip()
    path.write_text(f"---\n{fm}\n---\n{body.lstrip()}", encoding="utf-8")


def now():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="minutes")


def findings_for(body: str, ref: str):
    """Return (present, count) for the `## Findings — <step>` block of this step."""
    m = re.search(rf"^## Findings — {re.escape(ref)}\s*$(.*?)(?=^## |\Z)", body, re.M | re.S)
    if not m:
        return False, 0
    lines = [l.strip() for l in m.group(1).splitlines() if l.strip()]
    if not lines or (len(lines) == 1 and lines[0].strip("-* ").casefold() in ("none", "no findings")):
        return True, 0
    return True, len([l for l in lines if l.startswith(("-", "*", "1", "2", "3", "4", "5", "6", "7", "8", "9"))]) or len(lines)


def set_state(meta, roles, workflows, step, lane=None):
    cfg = roles["steps"][step]
    w, s = step_of(workflows, step)
    meta["step"] = step
    meta["mode"] = "closed" if s.get("type") == "end" else cfg["mode"]
    meta["role"] = cfg["role"]
    meta["waiting_on"] = "nobody" if s.get("type") == "end" else ("PM" if cfg["mode"] == "pm" else "AI")
    meta["since"] = now()
    if lane:
        meta["lane"] = lane
    meta.setdefault("lane", "full")
    meta.setdefault("failed_passes", 0)
    meta["rerun_count"] = 0
    return meta


def resolve_target(ex, to):
    """--to may be a full ref, its bare step id, a 1-based index, or a unique prefix of the target."""
    to = to.strip()
    if not to:
        return None  # an empty --to would prefix-match a single exit
    if to.isdigit() and 1 <= int(to) <= len(ex):
        return ex[int(to) - 1][0]
    hits = [t for t, _ in ex if t == to] or [t for t, _ in ex if t.partition(".")[2] == to] or [t for t, _ in ex if t.startswith(to)]
    return hits[0] if len(hits) == 1 else None


def resolve_when(ex, tgt, when):
    """--when may be the condition, a 1-based index, or a unique prefix; returns canonical text or None."""
    canon = dict(ex)[tgt]
    if not canon or canon == "handoff":
        return canon
    if when is None:
        return None
    if when.isdigit():
        return canon if 1 <= int(when) <= len(ex) and ex[int(when) - 1][0] == tgt else None
    return canon if norm(canon) == norm(when) or norm(canon).startswith(norm(when)) and len(norm(when)) >= 6 else None


def template_for(commands, ref):
    """The command that enters this step and its template file, if any (entry commands first, else the first named)."""
    hits = [n for n, c in commands.items() if c.get("enters") == ref]
    if not hits:
        return None, None
    name = hits[0]
    path = FW / "commands" / f"{name}.md"
    return name, (str(path.relative_to(ROOT)) if path.exists() else None)


def next_info(meta, body, workflows, roles, commands) -> dict:
    """Everything `next` knows, as one dict (the runner reads this as JSON)."""
    ref = meta["step"]
    w, s = step_of(workflows, ref)
    cfg = roles["steps"][ref]
    info = {
        "step": ref, "title": s["title"], "type": s.get("type", "step"),
        "mode": cfg["mode"], "role": cfg["role"], "role_card": roles["roles"].get(cfg["role"]),
        "waiting_on": meta.get("waiting_on"), "lane": meta.get("lane"), "since": meta.get("since"),
        "closed": s.get("type") == "end",
        "inputs": list(cfg.get("inputs") or []),
        "what": (s.get("what") or "").strip(), "output": (s.get("output") or "").strip(),
        "notes": (s.get("notes") or "").strip(), "input": (s.get("input") or "").strip(),
        "failed_passes": int(meta.get("failed_passes", 0)), "rerun_count": int(meta.get("rerun_count", 0)),
        "exits": [{"index": i, "to": tgt, "when": None if when == "handoff" else when}
                  for i, (tgt, when) in enumerate(exits(workflows, ref), 1)],
        # the runner checks every move against these: how many edges the record has taken, and the last few
        "edges": len(meta.get("history") or []),
        "last_edges": list(meta.get("history") or [])[-5:],
    }
    name, path = template_for(commands, ref)
    info["command"] = name
    info["template"] = path
    if cfg["mode"] == "challenger":
        fr = cfg["framings"]
        info["framing"] = fr[min(int(meta.get("rerun_count", 0)), len(fr) - 1)]
        present, count = findings_for(body, ref)
        info["findings"] = {"present": present, "count": count}
    return info


def cmd_next(args, workflows, roles, commands):
    meta, body = read_record(Path(args.record))
    ref = meta.get("step")
    if not ref:
        print("record has no state; use `start`")
        return 1
    if ref not in roles["steps"]:
        print(f"refused: record is at unknown step {ref}")
        return 1
    w, s = step_of(workflows, ref)
    cfg = roles["steps"][ref]
    if getattr(args, "json", False):
        print(json.dumps(next_info(meta, body, workflows, roles, commands), ensure_ascii=False, indent=2))
        return 0
    print(f"step:     {ref} — {s['title']}")
    print(f"mode:     {meta.get('mode')}   role: {cfg['role']}   lane: {meta.get('lane')}   waiting on: {meta.get('waiting_on')} since {meta.get('since')}")
    print(f"inputs:   {', '.join(cfg['inputs'])}")
    if cfg["mode"] == "challenger":
        fr = cfg["framings"]
        idx = min(int(meta.get("rerun_count", 0)), len(fr) - 1)
        present, count = findings_for(body, ref)
        print(f"framing:  {fr[idx]}" + ("  (rerun)" if meta.get("rerun_count") else ""))
        print(f"findings: block {'present' if present else 'MISSING'}, {count} finding(s); write `## Findings — {ref}` before leaving; zero findings in the full lane → `rerun`")
    if s.get("input"):
        print(f"PM gives: {s['input'].strip()}  → record it with `advance --answer`")
    print(f"does:     {(s.get('what') or '').strip()}")
    if s.get("output"):
        print(f"produces: {s['output'].strip()}")
    ex = exits(workflows, ref)
    if ex:
        print("exits:")
        for i, (tgt, when) in enumerate(ex, 1):
            print(f"  {i}. → {tgt}" + (f"   when: {when}" if when and when != "handoff" else ""))
    else:
        print("exits:    none — this record is closed here")
    if ref == "deliver.passes":
        print(f"failed passes so far: {meta.get('failed_passes', 0)} ({MAX_FAILED} → only plan is legal)")
    hist = meta.get("history") or []
    if hist:
        print("last edges:")
        for h in hist[-4:]:
            print(f"  {h['from']} → {h['to']}" + (f"  ({h['when']})" if h.get("when") else "") + (f"  answer: {h['answer']}" if h.get("answer") else ""))
    return 0


def cmd_advance(args, workflows, roles, commands):
    path = Path(args.record)
    meta, body = read_record(path)
    ref = meta.get("step")
    if not ref or ref not in roles["steps"]:
        print("refused: record has no state or is at an unknown step; use `start` / fix the record")
        return 1
    w, s = step_of(workflows, ref)
    cfg = roles["steps"][ref]
    ex = exits(workflows, ref)
    if not ex:
        print(f"refused: {ref} is an end; the record is closed")
        return 1
    tgt = resolve_target(ex, args.to)
    if not tgt:
        print(f"refused: {ref} has no edge to {args.to}. Legal exits: " + ", ".join(f"{i}. {t}" for i, (t, _) in enumerate(ex, 1)))
        return 1
    canon = dict(ex)[tgt]
    when = resolve_when(ex, tgt, args.when)
    if canon and canon != "handoff" and when is None:
        print(f"refused: the edge {ref} → {tgt} is taken when \"{canon}\"; pass --when with that condition (or its number)")
        return 1
    if (not canon or canon == "handoff") and args.when:
        print(f"refused: {ref} → {tgt} has no condition; drop --when")
        return 1
    # gate artefacts
    if cfg["mode"] == "pm" and not args.answer:
        print(f"refused: {ref} is a PM step; record the PM's answer with --answer \"…\"")
        return 1
    if cfg["mode"] == "challenger":
        present, count = findings_for(body, ref)
        if not present:
            print(f"refused: write the block `## Findings — {ref}` into the record before leaving (a line \"none\" if nothing was found)")
            return 1
        if count == 0 and meta.get("lane") != "small" and int(meta.get("rerun_count", 0)) < len(cfg["framings"]) - 1:
            print(f"refused: zero findings on the full lane with framings left; run `rerun` and challenge again")
            return 1
    # lane
    if args.lane and ref != "define.sort":
        print("refused: --lane is set only at start or when leaving define.sort")
        return 1
    # failed passes
    failed = int(meta.get("failed_passes", 0))
    if ref == "deliver.passes":
        if tgt == "deliver.execute":
            if failed >= MAX_FAILED:
                print(f"refused: {MAX_FAILED} passes have failed; the only legal exit is deliver.plan")
                return 1
            failed += 1
        if tgt == "deliver.accept" and failed >= MAX_FAILED:
            print(f"refused: {MAX_FAILED} passes have failed; go to deliver.plan")
            return 1
    hist = meta.get("history") or []
    entry = {"from": ref, "to": tgt, "when": None if canon == "handoff" else canon, "at": now()}
    if args.answer:
        entry["answer"] = args.answer
    if args.lane:
        entry["lane"] = args.lane
    closure = local_closure(workflows, ref)
    if closure:
        entry["closes"] = closure
    hist.append(entry)
    meta["history"] = hist
    meta["failed_passes"] = 0 if tgt == "deliver.plan" else failed
    set_state(meta, roles, workflows, tgt, lane=args.lane)
    write_record(path, meta, body)
    print(f"{ref} → {tgt}" + (f"  (when: {canon})" if canon and canon != "handoff" else "") + (f"  [closes {closure}]" if closure else ""))
    return cmd_next(argparse.Namespace(record=args.record), workflows, roles, commands)


def cmd_start(args, workflows, roles, commands):
    path = Path(args.record)
    c = commands.get(args.command)
    if not c:
        print(f"unknown command {args.command}; known: {', '.join(commands)}")
        return 1
    meta, body = read_record(path) if path.exists() else ({}, f"# {path.stem}\n\n## Request\n\n")
    if c.get("meta"):
        print(f"refused: {args.command} is a meta command (it runs the record at its current step); use `python3 framework/tools/run.py {args.record}`")
        return 1
    if not c.get("entry"):
        if meta.get("step") == c["enters"]:
            print(f"{args.command} continues the record at {c['enters']}:")
            return cmd_next(argparse.Namespace(record=args.record), workflows, roles, commands)
        print(f"refused: {args.command} is not an entry command; it continues a record already at {c['enters']} (this one is at {meta.get('step') or 'no state'}). New requests start with speckit.specify.")
        return 1
    if meta.get("step"):
        print(f"refused: record already at {meta['step']}; use `advance`")
        return 1
    meta["command"] = args.command
    meta["history"] = []
    set_state(meta, roles, workflows, c["enters"], lane=args.lane or "full")
    path.parent.mkdir(parents=True, exist_ok=True)  # changes/ is the documented location; create it on the first record
    write_record(path, meta, body)
    print(f"started at {c['enters']} via {args.command}")
    return cmd_next(argparse.Namespace(record=args.record), workflows, roles, commands)


def cmd_rerun(args, workflows, roles, commands):
    path = Path(args.record)
    meta, body = read_record(path)
    cfg = roles["steps"].get(meta.get("step"), {})
    if cfg.get("mode") != "challenger":
        print("refused: rerun applies only at a challenger step")
        return 1
    if meta.get("lane") == "small":
        print("refused: the small lane never reruns a challenge")
        return 1
    n = int(meta.get("rerun_count", 0)) + 1
    if n >= len(cfg["framings"]):
        print("refused: every framing has been used; leave with the findings you have (a \"none\" block is now accepted)")
        return 1
    meta["rerun_count"] = n
    write_record(path, meta, body)
    print(f"rerun {n}: framing → {cfg['framings'][n]}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    p = sub.add_parser("next"); p.add_argument("record"); p.add_argument("--json", action="store_true", help="one JSON object for the runner")
    p = sub.add_parser("advance"); p.add_argument("record"); p.add_argument("--to", required=True); p.add_argument("--when"); p.add_argument("--answer"); p.add_argument("--lane", choices=["small", "full"])
    p = sub.add_parser("start"); p.add_argument("record"); p.add_argument("--command", required=True); p.add_argument("--lane", choices=["small", "full"])
    p = sub.add_parser("rerun"); p.add_argument("record")
    args = ap.parse_args()
    workflows, roles, commands = load_system()
    toolbox = load_toolbox()
    problems = check(workflows, roles, commands) + check_toolbox(workflows, toolbox)
    if args.cmd == "check":
        if problems:
            print(f"NOT CLOSED — {len(problems)} problem(s):")
            for x in problems:
                print("  -", x)
            return 1
        n = sum(len(w["steps"]) for w in workflows.values())
        meta_n = sum(1 for c in commands.values() if c.get("meta"))
        line = f"CLOSED — {n} steps, every one mapped to a role and mode; {len(commands) - meta_n} commands, every one entering a real non-routing step"
        if meta_n:
            line += f"; {meta_n} meta command entering the record's current step"
        if toolbox is not None:
            line += f"; toolbox: {len(toolbox.get('steps') or {})} step row(s)"
        print(line)
        return 0
    if problems:
        print("refused: the system is not closed; run `check`")
        return 1
    return {"next": cmd_next, "advance": cmd_advance, "start": cmd_start, "rerun": cmd_rerun}[args.cmd](args, workflows, roles, commands)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Refused as e:
        print(f"refused: {e}")
        sys.exit(1)
    except BrokenPipeError:
        sys.exit(0)
