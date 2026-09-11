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
      move the record along one edge. Refuses: --answer at a step that is
      not a PM step (checked first: "<step> is an AI step, not a PM step; the
      runner (or the AI) moves it"); an exit not in the YAML; a decision
      without its condition; a mismatched condition; leaving a PM step
      without --answer; leaving a challenger step without a findings
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

Large requests (define.breakdown … define.spawn) and removals (define.impact):
  leaving define.breakdown needs a `## Breakdown — proposed <date>` block with
  numbered chunks (`  1. <slug> — <text>`, then `depends on:` and `why this
  line:`); leaving define.impact needs `## Impact — proposed <date>` with
  numbered dependants. The PM's --answer at define.confirm-breakdown /
  define.confirm-impact is appended verbatim as `## Breakdown — PM answer` /
  `## Impact — PM answer`; only a yes may go to spawn, anything else goes back
  to breakdown for a rewrite (the AI rewrites; spawn consumes a proposal + a
  yes). Each gate is reached at most three times, then only write or drop.
  Leaving define.spawn writes one child per chunk,
  changes/<date>-<n>.<chunk>-<slug>.md, with `parent`, `chunk`, `depends_on`
  (a chunk with no explicit dependency depends on the previous one); chunk 1
  at define.discuss, the others at the pseudo-step `waiting` (`waiting_on:
  chunk <n>`), released with `advance --to define.discuss` once every
  dependency is at deliver.done or dropped (E3). Also written: the group block
  in changes/QUEUE.md (refreshed on every child move) and the decision
  decisions/D-<nnnn>-breakdown-<parent-slug>.md. A child's `advance --to
  revise-breakdown` reopens the parent at define.confirm-breakdown with the
  child's discussion as a new proposed block; a re-spawn keeps existing
  children by slug (files and history), drops removed chunks, never touches a
  delivered one. Refused: `start` on a child (E10); next/advance/check on a
  child whose parent is missing or lacks the PM-answer block (E11); breakdown
  or impact without architecture.md (E6); impact while another record in
  Deliver names the same node (E18: `nodes:`, a task line's `[<id>]` tag, or
  backticks in this record); two chunks on one node with no dependency (E5);
  a slug colliding with an existing record, or one that cannot name a file;
  a chunk depending on a later chunk; a revision from a delivered chunk, or
  one that removes a chunk in Deliver or makes it wait (a chunk being built
  is never rewritten); spawn twice on one confirmation; write or drop from a
  reopened gate while children exist; a PM-answer block the gate never wrote;
  an impact block recommending delete for a store, or an impact answer that
  names no choice for a store (E19); a child edited past `waiting` by hand
  while a dependency is open (a dropped dependency hands its own on).
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
    # a child record: parent (relative path), chunk (int), depends_on (list of child paths) — read and preserved
    if "chunk" in meta and not (isinstance(meta["chunk"], int) and not isinstance(meta["chunk"], bool)):
        raise Refused(f"record field `chunk` must be an integer, not {meta['chunk']!r}")
    if "depends_on" in meta and not (isinstance(meta["depends_on"], list) and all(isinstance(x, str) for x in meta["depends_on"])):
        raise Refused("record field `depends_on` must be a list of record paths")
    if "parent" in meta and not isinstance(meta["parent"], str):
        raise Refused("record field `parent` must be the parent record's path")
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


# ---------------------------------------------------------------- groups: parent, children, waiting
WAITING = "waiting"                      # a child's pseudo-step; not in any YAML, handled in read/next/advance only
DEP_MET = {"deliver.done", "deliver.dropped", "define.dropped"}   # a dependency at one of these no longer blocks (E3)
GATE_CAP = 3                             # breakdown → confirm-breakdown (and impact → confirm-impact) at most this many times
RECORD_NAME = re.compile(r"^(\d{4}-\d{2}-\d{2})-(\d+)-([a-z0-9]+(?:-[a-z0-9]+)*)$")
CHUNK_LINE = re.compile(r"^\s*(\d+)\.\s+(\S+)\s+[—–-]+\s+(.*\S)\s*$")
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")   # a chunk slug names a file: lowercase letters, digits, hyphens; no path parts
YES_WORDS = "yes, y, ok, okay, confirm, confirmed, agreed, or \"yes, these chunks in this order\" (punctuation allowed, nothing else)"
TASK_TAG = re.compile(r"^\s*-\s*\[[ xX]\]\s*T\d+\s+(?:\[P\]\s+)?\[([A-Za-z0-9][\w-]*)\]", re.M)   # `- [ ] T001 [P] [node-id] …`: the node-id tag
TICK = re.compile(r"`([A-Za-z0-9][\w-]*)`")
DEP_LINE = re.compile(r"^\s*depends on\s*:\s*(.*)$", re.I)
WHY_LINE = re.compile(r"^\s*why this line\s*:\s*(.*)$", re.I)
HEADING = re.compile(r"^## (.+?)\s*$", re.M)
YES = re.compile(r"^(yes|y|ok|okay|confirm|confirmed|agreed)(?:[.!, ]+(these chunks(?: in this order)?|this order|as is|as proposed))?[.!]?$")


def rel(p: Path) -> str:
    """A path as the record files name each other: relative to the product root, posix."""
    try:
        return p.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return p.as_posix()


def try_read(p: Path):
    try:
        return read_record(p)
    except (Refused, yaml.YAMLError, OSError):
        return None, None


def title_of(body: str, path: Path) -> str:
    return next((l[2:].strip() for l in body.splitlines() if l.startswith("# ")), path.stem)


def sections(body: str):
    """[(title, text)] for every `## ` heading, in order."""
    heads = list(HEADING.finditer(body))
    out = []
    for i, h in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(body)
        out.append((h.group(1), body[h.end():end]))
    return out


def last_block(body: str, kind: str, part: str):
    """(index, title, text) of the last `## <Kind> — <part>…` section, or (None, None, None)."""
    pat = re.compile(rf"^{kind}\s*[—–-]\s*{part}\b", re.I)
    hit = (None, None, None)
    for i, (title, text) in enumerate(sections(body)):
        if pat.match(title):
            hit = (i, title, text)
    return hit


def parse_breakdown(text: str) -> dict:
    """The §3.3 block: chunks (n, slug, text, depends, depends_chunks, nodes, why), order, not_further, alternatives."""
    chunks, cur = [], None
    order = further = alts = ""
    for raw in text.splitlines():
        line = raw.rstrip()
        m = CHUNK_LINE.match(line)
        if m:
            cur = {"n": int(m.group(1)), "slug": m.group(2).casefold(), "text": m.group(3).strip(), "depends": "none", "why": ""}
            chunks.append(cur)
            continue
        low = line.strip().casefold()
        if low.startswith("order and reasons:"):
            order = line.split(":", 1)[1].strip(); cur = None
        elif low.startswith("not split further because:"):
            further = line.split(":", 1)[1].strip(); cur = None
        elif low.startswith("alternatives considered:"):
            alts = line.split(":", 1)[1].strip(); cur = None
        elif cur is not None and DEP_LINE.match(line):
            cur["depends"] = DEP_LINE.match(line).group(1).strip() or "none"
        elif cur is not None and WHY_LINE.match(line):
            cur["why"] = WHY_LINE.match(line).group(1).strip()
    for c in chunks:
        c["depends_chunks"] = sorted({int(x) for x in re.findall(r"\bchunk\s+(\d+)", c["depends"], re.I)})
        c["nodes"] = sorted({x.casefold() for x in re.findall(r"delivered node\s+([\w-]+)", c["depends"], re.I)}
                            | {x.casefold() for x in re.findall(r"`([\w-]+)`", c["text"])})
    return {"chunks": chunks, "order": order, "not_further": further,
            "alternatives": [a.strip().rstrip(".") for a in alts.split(";") if a.strip()]}


def parse_impact(text: str) -> dict:
    """The §3.4 block: the node removed and the dependants' node ids (numbered lines)."""
    removing = ""
    m = re.search(r"^\s*removing or changing\s*:\s*([\w-]+)", text, re.I | re.M)
    if m:
        removing = m.group(1)
    deps = [x.casefold() for x in re.findall(r"^\s*\d+\.\s+([A-Za-z0-9][\w-]*)", text, re.M)]
    # `Stored data: <table or field> — keep | migrate to <…> | delete; recommended: <…>`, one store per line (continuation
    # lines indented under it); "none" or "(none)" means no store. E19: the PM chooses per store; "delete" is never the default.
    stores = []
    m = re.search(r"^\s*stored data\s*:(.*?)(?=^\s*(?:possible, unverified|rules and decisions affected)\s*:|\Z)", text, re.I | re.M | re.S)
    if m:
        for raw in m.group(1).splitlines():
            line = raw.strip()
            if not line or re.fullmatch(r"\(?none[^)]*\)?\.?", line, re.I):
                continue
            parts = re.split(r"\s+[—–-]+\s+", line, 1)
            rec = re.search(r"recommended\s*:\s*(\w+)", parts[1] if len(parts) > 1 else "", re.I)
            stores.append({"name": parts[0].strip().strip("`"), "recommended": (rec.group(1).casefold() if rec else "")})
    return {"removing": removing, "dependants": deps, "stores": stores}


def validate_chunks(bd: dict, path) -> None:
    """The chunks of a proposed block, before anything consumes them: slugs that name a file (no path parts, no `..`),
    numbers 1..n, one slug per chunk, dependencies only on earlier chunks (dependencies first)."""
    chunks = bd["chunks"]
    for c in chunks:
        if not SLUG.match(c["slug"]):
            raise Refused(f"chunk {c['n']} in {path} has the slug {c['slug']!r}, which cannot name a record file; a slug is lowercase letters, digits and hyphens (no `/`, `..`, `_` or spaces)")
    nums = [c["n"] for c in chunks]
    if nums != list(range(1, len(nums) + 1)):
        raise Refused(f"the chunks in the last `## Breakdown — proposed` of {path} are numbered {nums}; they must run 1..{len(nums)} in the confirmed order")
    slugs = [c["slug"] for c in chunks]
    if len(set(slugs)) != len(slugs):
        raise Refused(f"two chunks share the slug {next(s for s in slugs if slugs.count(s) > 1)!r} in {path}; every chunk needs its own slug")
    for c in chunks:
        for d in c["depends_chunks"]:
            if d not in nums or d == c["n"]:
                raise Refused(f"chunk {c['n']} ({c['slug']}) depends on chunk {d}, which is not one of the other chunks 1..{len(nums)}")
            if d > c["n"]:
                raise Refused(f"chunk {c['n']} ({c['slug']}) depends on chunk {d}, which comes after it; dependencies first — reorder the chunks so every dependency precedes the chunk that needs it")


def is_yes(answer: str) -> bool:
    a = norm(answer).strip(" .!\"'")
    return bool(YES.match(a)) or a == norm("yes, these chunks in this order")


def confirmed_breakdown(body: str, path) -> dict:
    """The last `## Breakdown — proposed` block as confirmed by the last `## Breakdown — PM answer` (a yes).
    Anything but a yes is rewritten by the AI at define.breakdown, so spawn only ever consumes a proposal and a yes."""
    pi, ptitle, ptext = last_block(body, "Breakdown", "proposed")
    if pi is None:
        raise Refused(f"{path} has no `## Breakdown — proposed` block; define.breakdown writes it (format: framework/README, PLAN §3.3)")
    bd = parse_breakdown(ptext)
    if not bd["chunks"]:
        raise Refused(f"the block `## {ptitle}` in {path} lists no chunks; expected numbered lines `  1. <slug> — <capability>` with `depends on:` and `why this line:` under each")
    ai, atitle, atext = last_block(body, "Breakdown", "PM answer")
    if ai is None:
        raise Refused(f"{path} has no `## Breakdown — PM answer` block; the PM confirms at define.confirm-breakdown (advance --answer)")
    if ai < pi:
        raise Refused(f"the last `## {ptitle}` in {path} was written after the last `## {atitle}`; the PM has not confirmed this proposal (advance the record to define.confirm-breakdown and answer)")
    answer = atext.strip()
    if not is_yes(answer):
        raise Refused(f"the last `## {atitle}` in {path} is not a yes ({answer.splitlines()[0][:80]!r}); the AI rewrites the proposal from those words at define.breakdown (advance --to breakdown); spawn consumes only a proposal and a yes ({YES_WORDS})")
    bd["answer"] = answer
    return bd


def lane_for(chunk: dict) -> str:
    """E12: small when the chunk text names one node and no component; the heuristic reads the text."""
    t = chunk["text"].casefold()
    return "full" if ("component" in t or "new system" in t or len(chunk["nodes"]) > 1) else "small"


def slug_of(p: Path) -> str:
    """The slug of a record name: <date>-<n>-<slug> (a request) or <date>-<n>.<chunk>-<slug> (a child)."""
    return re.sub(r"^\d{4}-\d{2}-\d{2}-\d+(?:\.\d+)?-", "", p.stem).casefold()


def child_name(parent: Path, n: int, slug: str) -> Path:
    m = RECORD_NAME.match(parent.stem)
    if not m:
        raise Refused(f"parent record {rel(parent)} is not named <date>-<n>-<slug>.md; children are named from it")
    return parent.parent / f"{m.group(1)}-{m.group(2)}.{n}-{slug}.md"


def all_records():
    """Every change record under changes/ (not QUEUE.md, not the run logs): [(path, meta, body)]."""
    d = ROOT / "changes"
    out = []
    if not d.exists():
        return out
    for p in sorted(d.glob("*.md")):
        if p.name == "QUEUE.md":
            continue
        meta, body = try_read(p)
        if meta is not None and isinstance(meta, dict):
            out.append((p, meta, body))
    return out


def children_of(parent_rel: str):
    kids = [(p, m, b) for p, m, b in all_records() if m.get("parent") == parent_rel]
    return sorted(kids, key=lambda x: (str(x[1].get("step")) in ("define.dropped", "deliver.dropped"), int(x[1].get("chunk") or 0), x[0].name))


def check_parent(meta: dict, path: Path):
    """E11: a child is only readable while its parent and the PM's answer block exist."""
    if not meta.get("parent"):
        return None
    pp = ROOT / str(meta["parent"])
    if not pp.exists():
        raise Refused(f"{rel(path)} is chunk {meta.get('chunk')} of {meta['parent']}, which does not exist (E11); restore the parent file (it was moved or deleted by hand)")
    pmeta, pbody = try_read(pp)
    if pmeta is None:
        raise Refused(f"parent {meta['parent']} of {rel(path)} cannot be read (E11); fix its front matter")
    if last_block(pbody, "Breakdown", "PM answer")[0] is None:
        raise Refused(f"parent {meta['parent']} of {rel(path)} has no `## Breakdown — PM answer` block (E11); the parent was edited by hand — restore the block the PM answered at define.confirm-breakdown")
    step = str(meta.get("step"))
    if step not in (WAITING, "define.handed-over") and step not in DEP_MET:
        blocked = blocking_deps(meta)
        if blocked:
            c, p, s = blocked[0]
            who = f"chunk {c}" if c is not None else p
            raise Refused(f"{rel(path)} is chunk {meta.get('chunk')} of {meta['parent']} at {step}, but it depends on {who} ({p} at {s}, not deliver.done); "
                          f"a chunk leaves `waiting` only by `advance --to define.discuss` once every dependency is delivered or dropped — the record was edited by hand; set `step: waiting` and `mode: waiting` back")
    return pp, pmeta, pbody


def blocking_deps(meta: dict):
    """The dependencies that still block a waiting child: [(chunk, path, step)]; a dependency at deliver.done or dropped is met (E3).
    A dropped dependency hands its own dependencies on: a chunk that waited on a dropped middle chunk waits on what that chunk waited on."""
    out, seen, todo = [], set(), list(meta.get("depends_on") or [])
    while todo:
        dep = str(todo.pop(0))
        if dep in seen:
            continue
        seen.add(dep)
        dmeta, _ = try_read(ROOT / dep)
        if dmeta is None:
            out.append((None, dep, "missing"))
            continue
        step = str(dmeta.get("step"))
        if step in ("define.dropped", "deliver.dropped"):
            todo += [str(d) for d in (dmeta.get("depends_on") or []) if isinstance(d, str)]
        elif step not in DEP_MET:
            out.append((dmeta.get("chunk"), dep, step))
    return out


def wait_text(meta: dict) -> str:
    b = blocking_deps(meta)
    if not b:
        return "every dependency is delivered or dropped; release it with `advance --to define.discuss`"
    c, p, s = b[0]
    who = f"chunk {c}" if c is not None else p
    return f"{who} ({p} at {s}) to reach deliver.done" + (f"; then {len(b) - 1} more" if len(b) > 1 else "")


def live_wait(meta: dict) -> str:
    """The `waiting on` column of the group block: for a waiting child, its first still-blocking dependency as of now
    (the front matter's `waiting_on` moves only at the next release attempt); `release` when nothing blocks it any more."""
    if meta.get("step") != WAITING:
        return str(meta.get("waiting_on"))
    b = blocking_deps(meta)
    if not b:
        return "release"
    return f"chunk {b[0][0]}" if b[0][0] is not None else b[0][1]


def group_info(parent_rel: str):
    pp = ROOT / parent_rel
    pmeta, pbody = try_read(pp)
    if pmeta is None:
        return None
    kids = children_of(parent_rel)
    rows = [{"chunk": m.get("chunk"), "file": rel(p), "step": m.get("step"), "waiting_on": live_wait(m), "lane": m.get("lane")}
            for p, m, _ in kids]
    delivered = sum(1 for r in rows if r["step"] == "deliver.done")
    dropped = sum(1 for r in rows if r["step"] in ("deliver.dropped", "define.dropped"))
    in_flight = [r["chunk"] for r in rows if r["step"] not in DEP_MET and r["step"] != WAITING]
    return {"parent": parent_rel, "title": title_of(pbody, pp), "parent_step": pmeta.get("step"), "chunks": rows,
            "delivered": delivered, "dropped": dropped, "total": len(rows), "in_flight": in_flight}


def write_group_block(parent_rel: str):
    """The group block in changes/QUEUE.md, fenced by `<!-- group: <parent> -->` … `<!-- /group -->`; rewritten in place.
    Written at spawn and on every `advance` of a child or of the parent (framework/components/change-record.md documents it):
    `## Group: <parent title>`, `Parent: <path> (<step>)`, the chunk table (n | file | step | waiting on; dropped chunks last),
    then `<n> of <m> delivered[; <k> dropped]; in flight: chunk …|nothing in flight[; group closed[ dropped]]`."""
    g = group_info(parent_rel)
    if g is None:
        return
    lines = [f"<!-- group: {parent_rel} -->", f"## Group: {g['title']}", "",
             f"Parent: {parent_rel} ({g['parent_step']})", "",
             "| n | file | step | waiting on |", "|---|---|---|---|"]
    for r in g["chunks"]:
        lines.append(f"| {r['chunk']} | {r['file']} | {r['step']} | {r['waiting_on']} |")
    tail = f"{g['delivered']} of {g['total']} delivered"
    if g["dropped"]:
        tail += f"; {g['dropped']} dropped"
    tail += ("; in flight: " + ", ".join(f"chunk {c}" for c in g["in_flight"])) if g["in_flight"] else "; nothing in flight"
    if g["delivered"] + g["dropped"] == g["total"] and g["total"]:
        tail += "; group closed" + (" dropped" if g["delivered"] == 0 else "")
    lines += ["", tail, "<!-- /group -->"]
    block = "\n".join(lines)
    q = ROOT / "changes" / "QUEUE.md"
    text = q.read_text(encoding="utf-8") if q.exists() else "# Queue\n"
    note = ""
    pat = re.compile(rf"<!-- group: {re.escape(parent_rel)} -->(?:(?!<!-- group: ).)*?<!-- /group -->", re.S)
    if pat.search(text):
        text = pat.sub(lambda _m: block, text, count=1)
    elif f"<!-- group: {parent_rel} -->" in text:
        # the closing fence was removed by hand: rewrite from the opening fence to the next group (or the end)
        pat = re.compile(rf"<!-- group: {re.escape(parent_rel)} -->(?:(?!<!-- group: ).)*", re.S)
        text = pat.sub(lambda _m: block + "\n", text, count=1).rstrip("\n") + "\n"
        note = f"  changes/QUEUE.md: the group block for {parent_rel} had no closing fence (edited by hand); rewritten"
    else:
        text = text.rstrip("\n") + "\n\n" + block + "\n"
    q.parent.mkdir(parents=True, exist_ok=True)
    q.write_text(text, encoding="utf-8")
    if note:
        print(note)


def next_decision_id() -> str:
    d = ROOT / "decisions"
    ids = [int(m.group(1)) for p in (d.glob("D-*.md") if d.exists() else []) for m in [re.match(r"^D-(\d{4})-", p.name)] if m]
    return f"D-{(max(ids) + 1 if ids else 1):04d}"


def write_breakdown_decision(parent: Path, pmeta: dict, pbody: str, bd: dict, kids) -> Path:
    """decisions/D-<nnnn>-breakdown-<parent-slug>.md in decision-log.md format; a re-spawn supersedes the earlier one."""
    d = ROOT / "decisions"
    d.mkdir(parents=True, exist_ok=True)
    parent_rel = rel(parent)
    slug = RECORD_NAME.match(parent.stem).group(3)
    did = next_decision_id()
    earlier = None
    for p in sorted(d.glob("D-*.md")):
        m, _ = try_read(p)
        if m and str(m.get("record")) == parent_rel and m.get("at_step") == "define.confirm-breakdown" and not m.get("superseded_by"):
            earlier = p
    title = title_of(pbody, parent)
    n = len(bd["chunks"])
    fm = [f'made_at: "{now()}"', "category: product", "made_by: PM", "at_step: define.confirm-breakdown",
          f"record: {parent_rel}", "nodes: [" + ", ".join(c["slug"] for c in bd["chunks"]) + "]"]
    if earlier:
        fm.append(f"supersedes: {earlier.name[:6]}")
    lines = ["---"] + fm + ["---", f"# Breakdown of {title}: {n} chunk{'s' if n != 1 else ''} in the confirmed order", "",
             "## Situation", "",
             f"The request in {parent_rel} named several capabilities. At define.confirm-breakdown the PM read the proposed chunks, "
             f"their dependencies, the order and the alternatives, and answered: {bd['answer'].splitlines()[0]}", "",
             "## Decision", ""]
    for c, (kp, km, _) in zip(bd["chunks"], kids):
        lines.append(f"{c['n']}. {c['slug']} — {c['text']} (depends on: {c['depends']}; record {rel(kp)})")
    if bd["order"]:
        lines += ["", f"Order and reasons: {bd['order']}"]
    lines += ["", "## Reasons", ""]
    if bd["not_further"]:
        lines.append(f"Not split further because: {bd['not_further']}")
    alts = bd["alternatives"] or ["one node for the whole request"]
    for a in alts:
        lines.append(f"- Instead of {a[0].lower() + a[1:] if a[:1].isupper() and not a[:2].isupper() else a}, the request is built as these {n} chunk{'s' if n != 1 else ''}.")
    if earlier:
        lines.append(f"- Instead of the breakdown in {earlier.name[:6]}, this revision stands; delivered chunks are untouched.")
    out = d / f"{did}-breakdown-{slug}.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if earlier:
        text = earlier.read_text(encoding="utf-8")
        earlier.write_text(text.replace("\n---\n", f"\nsuperseded_by: {did}\n---\n", 1), encoding="utf-8")
    return out


def child_state(meta: dict, roles, workflows, chunk: dict, first: bool, lane: str, from_step: str):
    """Chunk 1 at define.discuss; the others at the `waiting` pseudo-step, waiting on their first unmet dependency."""
    if first:
        set_state(meta, roles, workflows, "define.discuss", lane=lane)
        meta["history"] = list(meta.get("history") or []) + [{"from": from_step, "to": "define.discuss", "when": None, "at": now()}]
        return
    meta["step"] = WAITING
    meta["mode"] = WAITING
    meta["role"] = "Sorter"
    b = blocking_deps(meta)
    meta["waiting_on"] = (f"chunk {b[0][0]}" if b and b[0][0] is not None else (b[0][1] if b else "release"))
    meta["since"] = now()
    meta["lane"] = lane
    meta.setdefault("failed_passes", 0)
    meta["rerun_count"] = 0
    meta["history"] = list(meta.get("history") or []) + [{"from": from_step, "to": WAITING, "when": None, "at": now()}]


def plan_spawn(parent: Path, pmeta: dict, pbody: str):
    """Every refusal of define.spawn, before anything is written. Returns (bd, plan) where plan is [(child_path, chunk, existing_meta_or_None)]."""
    if pmeta.get("parent"):
        raise Refused(f"{rel(parent)} is itself a child (chunk {pmeta.get('chunk')} of {pmeta['parent']}); a chunk is never broken down further — say so at define.discuss and use revise-breakdown on the parent")
    # spawn twice: the confirmed answer was already consumed (every yes at the gate is followed by one spawn → broken-down)
    yeses = gate_rounds(pmeta, "define.confirm-breakdown", "define.spawn")
    spawned = gate_rounds(pmeta, "define.spawn", "define.broken-down")
    if spawned >= yeses:
        raise Refused(f"the breakdown confirmed in the last `## Breakdown — PM answer` of {rel(parent)} was already spawned ({spawned} spawn(s) for {yeses} yes(es) in the history; "
                      f"its group block is in changes/QUEUE.md); spawn runs once per confirmation — to change the chunks, use revise-breakdown from a chunk still in Define")
    check_answers_genuine(pmeta, pbody, "Breakdown", "define.confirm-breakdown", rel(parent))
    bd = confirmed_breakdown(pbody, rel(parent))
    chunks = bd["chunks"]
    validate_chunks(bd, rel(parent))
    nums = [c["n"] for c in chunks]
    # E5: two chunks on one node without an explicit dependency between them
    for i, a in enumerate(chunks):
        for b in chunks[i + 1:]:
            shared = sorted(set(a["nodes"]) & set(b["nodes"]))
            if shared and a["n"] not in b["depends_chunks"] and b["n"] not in a["depends_chunks"]:
                raise Refused(f"chunks {a['n']} ({a['slug']}) and {b['n']} ({b['slug']}) both touch node {shared[0]} with no dependency between them (E5); "
                              f"add `depends on: chunk {a['n']}` to chunk {b['n']} (a node is named as `delivered node <id>` or as `<id>` in backticks)")
    parent_rel = rel(parent)
    mine = {}   # slug → (path, meta) of this parent's existing children: a revision keeps their files and history (E4)
    for q, m, _ in children_of(parent_rel):
        mine.setdefault(slug_of(q), (q, m))
    plan = []
    # a chunk mid-Deliver is never rewritten by a revision (its plan is approved, its code in progress): it must stay in the
    # set, with every dependency the revision gives it already met; else the revision waits for it (deliver.done) or the PM drops it at its gate
    building = {s: (q, m) for s, (q, m) in mine.items() if str(m.get("step")).startswith("deliver.") and str(m.get("step")) not in DEP_MET}
    for s, (q, m) in building.items():
        if s not in [c["slug"] for c in chunks]:
            raise Refused(f"chunk {m.get('chunk')} ({s}) is in Deliver ({m.get('step')}, {rel(q)}); a revision never rewrites or removes a chunk being built — "
                          f"keep it in the proposal, wait for it to reach deliver.done, or drop it at its own gate")
    by_n = {c["n"]: c for c in chunks}
    for c in chunks:
        if c["slug"] in building:
            for d in c["depends_chunks"] or ([c["n"] - 1] if c["n"] > 1 else []):
                ds = by_n[d]["slug"]
                dm = mine.get(ds, (None, {}))[1]
                if str(dm.get("step")) not in DEP_MET:
                    raise Refused(f"chunk {c['n']} ({c['slug']}) is in Deliver ({building[c['slug']][1].get('step')}) and the revision makes it depend on chunk {d} ({ds}), "
                                  f"which is not delivered; a chunk being built cannot wait — order it before the chunks that are not delivered yet")
        if c["slug"] in mine:
            plan.append((mine[c["slug"]][0], c, mine[c["slug"]][1]))
            continue
        p = child_name(parent, c["n"], c["slug"])
        if p.exists():
            raise Refused(f"chunk {c['n']} would be written to {rel(p)}, which already exists and is not a child of {parent_rel}; choose another slug for the chunk")
        other = [q for q, m, _ in all_records() if q != parent and slug_of(q) == c["slug"]]
        if other:
            raise Refused(f"chunk {c['n']} ({c['slug']}) collides with the existing record {rel(other[0])} (same slug); choose another slug for the chunk")
        plan.append((p, c, None))
    return bd, plan


def do_spawn(parent: Path, pmeta: dict, pbody: str, roles, workflows, bd: dict, plan):
    """Write the children (a revision keeps existing files and history), the decision file and the group block."""
    parent_rel = rel(parent)
    paths = {c["n"]: rel(p) for p, c, _ in plan}
    ptitle = title_of(pbody, parent)
    m = len(plan)
    written = []
    for p, c, existing in plan:
        deps = [paths[d] for d in c["depends_chunks"]] or ([paths[c["n"] - 1]] if c["n"] > 1 else [])
        if existing is not None and (str(existing.get("step")) in DEP_MET or str(existing.get("step")).startswith("deliver.")):
            meta, body = read_record(p)          # a delivered, dropped or mid-Deliver chunk is never touched (only its number and dependencies follow the order)
            meta["chunk"] = c["n"]
            meta["depends_on"] = deps
            write_record(p, meta, body)
            written.append((p, meta, body))
            continue
        if existing is not None:
            meta, body = read_record(p)
            from_step = str(meta.get("step"))
        else:
            meta, from_step = {"command": pmeta.get("command")}, "define.spawn"
            body = (f"# {c['text']}\n\n## Request\n\n{c['text']}\n\nChunk {c['n']} of {m} of \"{ptitle}\" (parent: {parent_rel}).\n"
                    f"Depends on: {c['depends']}.\n" + (f"Why this line: {c['why']}\n" if c["why"] else ""))
        meta["parent"] = parent_rel
        meta["chunk"] = c["n"]
        meta["depends_on"] = deps
        child_state(meta, roles, workflows, c, not deps, lane_for(c), from_step)
        write_record(p, meta, body)
        written.append((p, meta, body))
    # a revision: chunks no longer in the set are dropped with the reason (delivered ones untouched)
    keep = {rel(p) for p, _, _ in plan}
    for q, qm, qb in children_of(parent_rel):
        if rel(q) in keep or str(qm.get("step")) in DEP_MET:
            continue
        qm["history"] = list(qm.get("history") or []) + [{"from": str(qm.get("step")), "to": "define.dropped", "when": "removed by the revised breakdown", "at": now()}]
        set_state(qm, roles, workflows, "define.dropped")
        qm["waiting_on"] = "nobody"
        write_record(q, qm, qb + f"\n## Outcome\n\ndropped: removed by the revised breakdown confirmed in {parent_rel}\n")
    dec = write_breakdown_decision(parent, pmeta, pbody, bd, written)
    write_group_block(parent_rel)
    return written, dec


def check_answers_genuine(meta: dict, body: str, kind: str, gate: str, path) -> None:
    """A `## <Kind> — PM answer` block is written only by `advance --answer` at the gate, so the body never carries more of
    them than the history has exits from that gate; more means the AI (or a hand edit) forged one — refused."""
    n_body = sum(1 for title, _ in sections(body) if re.match(rf"^{kind}\s*[—–-]\s*PM answer\b", title, re.I))
    n_hist = sum(1 for h in (meta.get("history") or []) if isinstance(h, dict) and h.get("from") == gate)
    if n_body > n_hist:
        raise Refused(f"{path} carries {n_body} `## {kind} — PM answer` block(s) but the PM has answered {gate} {n_hist} time(s); "
                      f"that block is written only by `advance --answer` at the gate — remove the one written by hand or by the AI")


def gate_rounds(meta: dict, frm: str, to: str) -> int:
    return sum(1 for h in (meta.get("history") or []) if h.get("from") == frm and h.get("to") == to)


def nodes_named(meta: dict, body: str, tasks_only: bool = False) -> set:
    """The node ids a record names: its front matter `nodes:` list, the `[node-id]` tag of every task line
    (`- [ ] T001 [P] [node-id] …`, the plan's grammar) and, unless tasks_only, every backticked `id` in its body and in
    the PM's answers in its history (the request as stated at intake lives there)."""
    out = {str(n).casefold() for n in (meta.get("nodes") or []) if isinstance(meta.get("nodes"), list)}
    out |= {x.casefold() for x in TASK_TAG.findall(body or "")}
    if not tasks_only:
        answers = "\n".join(str(h.get("answer") or "") for h in (meta.get("history") or []) if isinstance(h, dict))
        out |= {x.casefold() for x in TICK.findall((body or "") + "\n" + answers)}
    return out


def records_in_deliver_on(nodes) -> list:
    """E18: change records mid-Deliver that name one of these node ids (front matter `nodes:` or a task line's `[node-id]` tag)."""
    want = {str(n).casefold() for n in (nodes or [])}
    hits = []
    for p, m, b in all_records():
        step = str(m.get("step") or "")
        if step.startswith("deliver.") and step not in ("deliver.done", "deliver.dropped"):
            mine = nodes_named(m, b, tasks_only=True)
            if want & mine:
                hits.append((rel(p), step, sorted(want & mine)))
    return hits


def child_discussion(body: str) -> str:
    """The child's discussion notes: the last `## define.discuss` when present (a chunk re-discussed after a revision has
    several; the newest is the proposal), else the last section, else the body."""
    secs = sections(body)
    hits = [text for title, text in secs if norm(title) in ("define.discuss", "discussion", "discussion notes")]
    if hits:
        return hits[-1].strip()
    return secs[-1][1].strip() if secs else body.strip()


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


def next_info(meta, body, workflows, roles, commands, path=None) -> dict:
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
    name, tmpl = template_for(commands, ref)
    info["command"] = name
    info["template"] = tmpl
    if cfg["mode"] == "challenger":
        fr = cfg["framings"]
        info["framing"] = fr[min(int(meta.get("rerun_count", 0)), len(fr) - 1)]
        present, count = findings_for(body, ref)
        info["findings"] = {"present": present, "count": count}
    add_group_info(info, meta, path)
    return info


def add_group_info(info: dict, meta: dict, path=None):
    """parent, chunk, depends_on and the group block's data, for a child (or a parent with children)."""
    info["parent"] = meta.get("parent")
    info["chunk"] = meta.get("chunk")
    info["depends_on"] = list(meta.get("depends_on") or [])
    grp = meta.get("parent") or (rel(Path(path)) if path else None)
    info["group"] = group_info(grp) if grp else None
    if info["group"] is not None and not info["group"]["chunks"]:
        info["group"] = None


def waiting_info(meta: dict, path: Path) -> dict:
    """`next` for a child at the `waiting` pseudo-step (not a YAML step): the wait, and the one release exit."""
    info = {
        "step": WAITING, "title": f"Waiting on {meta.get('waiting_on')}", "type": WAITING, "mode": WAITING, "role": meta.get("role"),
        "role_card": None, "waiting_on": meta.get("waiting_on"), "lane": meta.get("lane"), "since": meta.get("since"),
        "closed": False, "inputs": [], "what": "", "output": "", "notes": "", "input": "",
        "failed_passes": int(meta.get("failed_passes", 0)), "rerun_count": int(meta.get("rerun_count", 0)),
        "exits": [{"index": 1, "to": "define.discuss", "when": "every dependency at deliver.done (or dropped)"}],
        "wait": wait_text(meta), "blocked_by": [{"chunk": c, "file": p, "step": s} for c, p, s in blocking_deps(meta)],
        "edges": len(meta.get("history") or []), "last_edges": list(meta.get("history") or [])[-5:],
        "command": None, "template": None,
    }
    add_group_info(info, meta, path)
    return info


def cmd_next(args, workflows, roles, commands):
    path = Path(args.record)
    meta, body = read_record(path)
    ref = meta.get("step")
    if not ref:
        print("record has no state; use `start`")
        return 1
    check_parent(meta, path)  # E11
    if ref == WAITING:
        if getattr(args, "json", False):
            print(json.dumps(waiting_info(meta, path), ensure_ascii=False, indent=2))
            return 0
        print(f"step:     waiting — chunk {meta.get('chunk')} of {meta.get('parent')}")
        print(f"mode:     waiting   role: {meta.get('role')}   lane: {meta.get('lane')}   waiting on: {meta.get('waiting_on')} since {meta.get('since')}")
        print(f"waits for: {wait_text(meta)}")
        print(f"depends on: {', '.join(meta.get('depends_on') or []) or 'nothing'}")
        print("exits:\n  1. → define.discuss   when: every dependency at deliver.done (or dropped); `advance --to define.discuss` releases it")
        return 0
    if ref not in roles["steps"]:
        print(f"refused: record is at unknown step {ref}")
        return 1
    w, s = step_of(workflows, ref)
    cfg = roles["steps"][ref]
    if getattr(args, "json", False):
        print(json.dumps(next_info(meta, body, workflows, roles, commands, path), ensure_ascii=False, indent=2))
        return 0
    print(f"step:     {ref} — {s['title']}")
    print(f"mode:     {meta.get('mode')}   role: {cfg['role']}   lane: {meta.get('lane')}   waiting on: {meta.get('waiting_on')} since {meta.get('since')}")
    if meta.get("parent"):
        print(f"chunk:    {meta.get('chunk')} of {meta['parent']}   depends on: {', '.join(meta.get('depends_on') or []) or 'nothing'}")
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


def advance_waiting(args, path: Path, meta: dict, body: str, workflows, roles, commands):
    """A waiting child has one exit, define.discuss, open only when every dependency is at deliver.done (or dropped, E3)."""
    if args.answer or args.lane:
        print("refused: a waiting child takes no --answer or --lane; it is released, not answered")
        return 1
    tgt = resolve_target([("define.discuss", None)], args.to)
    if tgt != "define.discuss":
        print(f"refused: a waiting child has one exit, define.discuss (advance --to define.discuss); not {args.to}")
        return 1
    blocked = blocking_deps(meta)
    if blocked:
        c, p, s = blocked[0]
        new_wait = f"chunk {c}" if c is not None else p
        if meta.get("waiting_on") != new_wait:   # a dropped or delivered dependency moves the wait to the next one
            moved = f"wait moved: {meta.get('waiting_on')} → {new_wait}"
            meta["waiting_on"] = new_wait
            meta["since"] = now()
            write_record(path, meta, body)
            write_group_block(str(meta["parent"]))
            print(moved)
        print(f"refused: chunk {meta.get('chunk')} waits on {new_wait} ({p} is at {s}, not deliver.done)" + (f"; {len(blocked) - 1} more dependency(ies) after it" if len(blocked) > 1 else ""))
        return 1
    hist = list(meta.get("history") or [])
    hist.append({"from": WAITING, "to": "define.discuss", "when": "released: every dependency at deliver.done or dropped", "at": now()})
    meta["history"] = hist
    set_state(meta, roles, workflows, "define.discuss")
    write_record(path, meta, body)
    write_group_block(str(meta["parent"]))
    print("waiting → define.discuss  (released: every dependency at deliver.done or dropped)")
    return cmd_next(argparse.Namespace(record=args.record), workflows, roles, commands)


def gate_checks(path: Path, meta: dict, body: str, ref: str, tgt: str, args) -> dict:
    """Every refusal the breakdown and impact paths add, before the edge is taken. Returns the side effects to apply
    after the state is written: {'body': new body, 'spawn': (bd, plan), 'revise': (parent_path, pmeta, pbody, section)}."""
    fx = {"body": body}
    recp = rel(path)
    # E6: no architecture file → neither breakdown nor impact
    if tgt in ("define.breakdown", "define.impact") and not (ROOT / "architecture.md").exists():
        raise Refused(f"{tgt.partition('.')[2]} needs architecture.md, which does not exist (E6); sort the request to to-foundation first, and propose the {tgt.partition('.')[2]} when Foundation has returned to define.discuss")
    # E18: a removal whose dependant is mid-Deliver waits for that record
    if tgt == "define.impact":
        hits = records_in_deliver_on(nodes_named(meta, body))
        if hits:
            p, s, shared = hits[0]
            raise Refused(f"{p} is in Deliver ({s}) on node {shared[0]}, which this request names (E18); one change in flight per node — the impact is shown once that record reaches deliver.done or is dropped "
                          "(heuristic: this record names a node in `nodes:`, in a task tag `[<id>]`, or in backticks in its body or its PM answers; the record in Deliver names it in `nodes:` or in a task line `- [ ] Tnnn [P] [<id>] …`; a record in Deliver with neither is not compared)")
    # revise-breakdown is a child's exit only; a delivered chunk is never revised
    if tgt == "define.revise-breakdown":
        if not meta.get("parent"):
            raise Refused(f"revise-breakdown is reached only from a child record (one with `parent:` in its front matter); {recp} is not a chunk")
        pp, pmeta, pbody = check_parent(meta, path)
        if not pbody.strip():
            raise Refused(f"parent {meta['parent']} is empty")
        fx["revise"] = (pp, pmeta, pbody, child_discussion(body))
    # leaving breakdown / impact needs the proposed block with content
    if ref == "define.breakdown":
        check_answers_genuine(meta, body, "Breakdown", "define.confirm-breakdown", recp)
        pi, ptitle, ptext = last_block(body, "Breakdown", "proposed")
        if pi is None:
            raise Refused(f"write the block `## Breakdown — proposed <date>` into {recp} before leaving define.breakdown (chunks as `  1. <slug> — <capability>`, each with `depends on:` and `why this line:`)")
        bd = parse_breakdown(ptext)
        if not bd["chunks"]:
            raise Refused(f"the block `## {ptitle}` in {recp} lists no chunks; expected numbered lines `  1. <slug> — <capability>` with `depends on:` and `why this line:` under each")
        validate_chunks(bd, recp)
    if ref == "define.impact":
        check_answers_genuine(meta, body, "Impact", "define.confirm-impact", recp)
        pi, ptitle, ptext = last_block(body, "Impact", "proposed")
        if pi is None:
            raise Refused(f"write the block `## Impact — proposed <date>` into {recp} before leaving define.impact (dependants as numbered lines `  1. <node id> [source]`)")
        im = parse_impact(ptext)
        if not im["dependants"]:
            raise Refused(f"the block `## {ptitle}` in {recp} lists no dependants; with no dependants there is no impact stop (E15): the request goes discuss → write and the node is retired as today")
        for st in im["stores"]:
            if st["recommended"] == "delete":
                raise Refused(f"the block `## {ptitle}` in {recp} recommends delete for the stored data {st['name']!r}; \"delete\" is never the default (E19) — recommend keep or migrate, the PM may still choose delete at define.confirm-impact")
    # the gates: the PM's answer is appended verbatim; the round cap; a yes goes to spawn and nowhere else
    if ref == "define.confirm-breakdown":
        n = gate_rounds(meta, "define.breakdown", "define.confirm-breakdown")
        if n >= GATE_CAP and tgt not in ("define.write", "define.drop"):
            raise Refused(f"the breakdown has been proposed {n} times (the cap is {GATE_CAP}); only write (one node) or drop are legal from define.confirm-breakdown now")
        if tgt in ("define.write", "define.drop") and children_of(recp):
            raise Refused(f"{recp} has children (the group block in changes/QUEUE.md); from the reopened gate only spawn (a yes, reconciled) or breakdown (a rewrite) are legal — "
                          f"to stop the group, drop each chunk at its own gate; to build the rest as one node, drop the chunks and start a new request")
        if tgt == "define.spawn" and not is_yes(args.answer):
            raise Refused(f"the PM's answer {args.answer.strip()[:80]!r} is not a yes ({YES_WORDS}); spawn consumes only a proposal and a yes — record it with --to breakdown (the AI rewrites the proposal from those words), --to write (one thing) or --to drop")
        if tgt == "define.breakdown" and is_yes(args.answer):
            raise Refused("the PM's answer is a yes; a yes goes to spawn (--to spawn --when 1), not back to breakdown")
        fx["body"] = body.rstrip("\n") + f"\n\n## Breakdown — PM answer {now()[:10]}\n\n{args.answer.strip()}\n"
    if ref == "define.confirm-impact":
        n = gate_rounds(meta, "define.impact", "define.confirm-impact")
        if n >= GATE_CAP and tgt not in ("define.write", "define.drop"):
            raise Refused(f"the impact has been proposed {n} times (the cap is {GATE_CAP}); only write or drop are legal from define.confirm-impact now")
        if tgt in ("define.write", "define.breakdown"):
            pi, ptitle, ptext = last_block(body, "Impact", "proposed")
            deps = parse_impact(ptext)["dependants"] if pi is not None else []
            if pi is None or not deps:
                raise Refused(f"{recp} has no `## Impact — proposed` block with dependants; the answer at define.confirm-impact cannot be parsed against it")
            missing = [d for d in deps if not re.search(rf"(?<![\w-]){re.escape(d)}(?![\w-])", args.answer, re.I)]
            if missing:
                raise Refused(f"the PM's answer names no choice for dependant {missing[0]!r} listed in `## {ptitle}` of {recp}; one line per dependant (retire it too | keep it by … | narrow the removal to … | postpone) and one per store of data (keep | migrate | delete)")
            for st in parse_impact(ptext)["stores"]:   # E19: the PM chooses per store; nothing is defaulted, delete least of all
                m = re.search(rf"{re.escape(st['name'])}\s*[:—–-]\s*(.*)", args.answer, re.I)
                if not m or not re.search(r"\b(keep|migrate|delete)\b", m.group(1).split(";")[0], re.I):
                    raise Refused(f"the PM's answer names no choice for the stored data {st['name']!r} listed in `## {ptitle}` of {recp} (E19); add `{st['name']}: keep | migrate to <…> | delete` — nothing is defaulted, delete least of all")
        fx["body"] = body.rstrip("\n") + f"\n\n## Impact — PM answer {now()[:10]}\n\n{args.answer.strip()}\n"
    # leaving spawn: the children are planned (every refusal) before the parent moves
    if ref == "define.spawn":
        fx["spawn"] = plan_spawn(path, meta, body)
    return fx


def cmd_advance(args, workflows, roles, commands):
    path = Path(args.record)
    meta, body = read_record(path)
    ref = meta.get("step")
    if ref and meta.get("parent"):
        check_parent(meta, path)  # E11
        if ref == WAITING:
            return advance_waiting(args, path, meta, body, workflows, roles, commands)
        if str(ref) in ("deliver.done",) and "revise" in (args.to or ""):
            print(f"refused: chunk {meta.get('chunk')} of {meta['parent']} is already delivered ({ref}); a delivered chunk is never revised — revise the breakdown from a chunk still in Define")
            return 1
    if not ref or ref not in roles["steps"]:
        print("refused: record has no state or is at an unknown step; use `start` / fix the record")
        return 1
    w, s = step_of(workflows, ref)
    cfg = roles["steps"][ref]
    ex = exits(workflows, ref)
    if not ex:
        print(f"refused: {ref} is an end; the record is closed")
        return 1
    if cfg["mode"] != "pm" and args.answer:
        # a person pasting the PM-stop command at a step the AI owns: say so before any --to / --when complaint
        print(f"refused: {ref} is an AI step, not a PM step; the runner (or the AI) moves it")
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
    # breakdown and impact: the gates' artefacts, the caps, spawn's plan, the revision (every refusal before the edge)
    fx = gate_checks(path, meta, body, ref, tgt, args)
    body = fx["body"]
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
    if "revise" in fx:
        meta["waiting_on"] = "parent"   # the child pauses until the parent's breakdown is confirmed again
    write_record(path, meta, body)
    # every file write before the first print: a closed stdout (a pipe to `head`) must not leave the group block stale
    out = [f"{ref} → {tgt}" + (f"  (when: {canon})" if canon and canon != "handoff" else "") + (f"  [closes {closure}]" if closure else "")]
    if "spawn" in fx:
        bd, plan = fx["spawn"]
        written, dec = do_spawn(path, meta, body, roles, workflows, bd, plan)
        for p, m, _ in written:
            out.append(f"  child {m['chunk']}: {rel(p)}  step: {m['step']}  waiting on: {m['waiting_on']}  lane: {m['lane']}  depends on: {', '.join(m.get('depends_on') or []) or 'nothing'}")
        out.append(f"  decision: {rel(dec)}   group block: changes/QUEUE.md")
    if "revise" in fx:
        pp, pmeta, pbody, section = fx["revise"]
        pmeta["history"] = list(pmeta.get("history") or []) + [{"from": str(pmeta.get("step")), "to": "define.confirm-breakdown",
                                                                "when": f"revise-breakdown from chunk {meta.get('chunk')} ({rel(path)})", "at": now()}]
        set_state(pmeta, roles, workflows, "define.confirm-breakdown")
        old = last_block(pbody, "Breakdown", "proposed")[2] or ""
        pbody = pbody.rstrip("\n") + (f"\n\n## Breakdown — proposed {now()[:10]}\n\nRevision proposed from chunk {meta.get('chunk')} ({rel(path)}): building it showed the split or the order is wrong.\n\n"
                                      f"{section}\n\n## Breakdown — previous chunks (for the PM's comparison)\n\n{old.strip()}\n")
        write_record(pp, pmeta, pbody)
        out.append(f"  parent {rel(pp)} reopened at define.confirm-breakdown with a new `## Breakdown — proposed` block; this chunk waits on parent")
    # the group block follows every move: of a child (its row, the counts) and of a parent with children (its step line)
    if meta.get("parent"):
        write_group_block(str(meta["parent"]))
    elif children_of(rel(path)):
        write_group_block(rel(path))
    print("\n".join(out))
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
    if meta.get("parent"):
        print(f"refused: {rel(path)} carries `parent: {meta['parent']}`; children are created by define.spawn; run the parent (E10)")
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
    p = sub.add_parser("check"); p.add_argument("record", nargs="?", help="also check this record's parent link (a child, E11)")
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
        if getattr(args, "record", None):
            meta, _ = read_record(Path(args.record))
            check_parent(meta, Path(args.record))  # E11
            if meta.get("parent"):
                line += f"; {rel(Path(args.record))} is chunk {meta.get('chunk')} of {meta['parent']} (parent and PM answer present)"
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
