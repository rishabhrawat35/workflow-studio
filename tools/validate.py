#!/usr/bin/env python3
"""Validate workflow-studio files against SCHEMA.md.

Usage:  python3 tools/validate.py            (run from repo root)
Exit code 0 = clean, 1 = errors printed.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
WF_DIR = ROOT / "workflows"
MAP = ROOT / "map.yaml"

ID_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
STEP_TYPES = {"step", "decision", "handoff", "end"}
WF_REQUIRED = ["id", "name", "owner", "purpose", "trigger", "steps"]
STEP_ALLOWED = {"id", "type", "title", "what", "notes", "next", "to", "owner", "input", "output"}
WF_ALLOWED = set(WF_REQUIRED)
MAP_ALLOWED = {"entry", "exit", "groups"}
GROUP_ALLOWED = {"id", "name", "workflows"}

errors: list[str] = []


def err(where: str, msg: str) -> None:
    errors.append(f"{where}: {msg}")


PARSE_ERROR = object()


class StrictLoader(yaml.SafeLoader):
    """SafeLoader that rejects duplicate mapping keys (PyYAML silently keeps the last one)."""

    def construct_mapping(self, node, deep=False):
        seen = set()
        for k_node, _ in node.value:
            if k_node.tag == "tag:yaml.org,2002:merge":
                continue  # `<<: *anchor` is expanded by the parent constructor; an explicit key may override a merged one
            k = self.construct_object(k_node, deep=deep)
            try:
                dup = k in seen
            except TypeError:
                raise yaml.constructor.ConstructorError(
                    "while constructing a mapping", node.start_mark, f"found unhashable key {k!r}", k_node.start_mark) from None
            if dup:
                raise yaml.constructor.ConstructorError(
                    "while constructing a mapping", node.start_mark, f"duplicate key {k!r}", k_node.start_mark)
            seen.add(k)
        return super().construct_mapping(node, deep)


def load_yaml(path: Path):
    """Return parsed content ({} for an empty file) or PARSE_ERROR."""
    try:
        with path.open(encoding="utf-8-sig") as f:
            data = yaml.load(f, Loader=StrictLoader)
        return {} if data is None else data
    except yaml.YAMLError as e:
        err(str(path.relative_to(ROOT)), f"YAML parse error: {e}")
        return PARSE_ERROR
    except UnicodeDecodeError as e:
        err(str(path.relative_to(ROOT)), f"not valid UTF-8 text: {e}")
        return PARSE_ERROR
    except OSError as e:
        err(str(path.relative_to(ROOT)), f"cannot read: {e}")
        return PARSE_ERROR


def blank(v) -> bool:
    """True for None, a non-string, or a string that is empty once stripped."""
    return not isinstance(v, str) or not v.strip()


def norm_next(step: dict, where: str, report: bool = True) -> list[tuple[str, str | None]]:
    """Return [(target_id, when|None)] and, when `report`, report shape errors."""
    rep = err if report else (lambda *_: None)
    out = []
    nxt = step.get("next")
    if nxt is None:
        return out
    if not isinstance(nxt, list) or not nxt:
        rep(where, "`next` must be a non-empty list")
        return out
    for item in nxt:
        if isinstance(item, str):
            out.append((item, None))
        elif isinstance(item, dict) and "to" in item:
            extra = set(item) - {"to", "when"}
            if extra:
                rep(where, f"unknown keys in next target: {sorted(extra)}")
            when = item.get("when")
            if when is not None and not isinstance(when, str):
                rep(where, f"`when` must be a string — quote it (YAML reads yes/no/on/off as booleans): {when!r}")
                when = None
            if not isinstance(item["to"], str):
                rep(where, f"next target `to` must be a step id string: {item['to']!r}")
                continue
            out.append((item["to"], when))
        else:
            rep(where, f"bad next target: {item!r}")
    seen_t = set()
    for t, when in out:
        if (t, when) in seen_t:
            rep(where, f"next target `{t}` listed twice with the same condition")
        seen_t.add((t, when))
    return out


def check_workflow(path: Path):
    rel = str(path.relative_to(ROOT))
    data = load_yaml(path)
    if data is PARSE_ERROR:
        return None
    if not isinstance(data, dict):
        err(rel, "top level must be a mapping")
        return None

    for k in WF_REQUIRED:
        if k not in data or data[k] in (None, "", []):
            err(rel, f"missing required field `{k}`")
        elif k != "steps" and not isinstance(data[k], str):
            err(rel, f"`{k}` must be a string (quote it): {data[k]!r}")
        elif k != "steps" and not data[k].strip():
            err(rel, f"`{k}` is blank")
    extra = set(data) - WF_ALLOWED
    if extra:
        err(rel, f"unknown workflow fields {sorted(extra)} — add to SCHEMA.md first")

    wid = data.get("id")
    if wid != path.stem:
        err(rel, f"id `{wid}` must equal filename `{path.stem}`")
    if isinstance(wid, str) and not ID_RE.match(wid):
        err(rel, f"id `{wid}` is not kebab-case")

    steps = data.get("steps") or []
    if not isinstance(steps, list):
        err(rel, "`steps` must be a list")
        return data

    ids: dict[str, dict] = {}
    targets_by_id: dict[str, list] = {}
    for i, s in enumerate(steps):
        where = f"{rel} step[{i}]"
        if not isinstance(s, dict):
            err(where, "must be a mapping")
            continue
        sid = s.get("id")
        where = f"{rel} step `{sid}`"
        if not isinstance(sid, str) or not ID_RE.match(sid):
            err(where, "missing or non-kebab-case id")
            continue
        if sid in ids:
            err(where, "duplicate step id")
        ids[sid] = s
        extra = set(s) - STEP_ALLOWED
        if extra:
            err(where, f"unknown step fields {sorted(extra)} — add to SCHEMA.md first")
        t = s.get("type")
        if t not in STEP_TYPES:
            err(where, f"type must be one of {sorted(STEP_TYPES)}")
        for k in ("title", "what", "notes", "owner", "input", "output"):
            if k in s and not isinstance(s[k], str):
                err(where, f"`{k}` must be a string (quote it): {s[k]!r}")
            elif k in s and not s[k].strip():
                err(where, f"`{k}` is blank — fill it in or remove the field")
        if "title" not in s:
            err(where, "missing `title`")
        if t != "end" and "what" not in s:
            err(where, "missing `what`")
        if "owner" in s and s["owner"] == data.get("owner"):
            err(where, "step owner repeats the workflow owner — remove it")

        if "input" in s and s.get("owner", data.get("owner")) != "PM":
            err(where, "`input` is only allowed on PM-owned steps")
        targets = norm_next(s, where)
        targets_by_id[sid] = targets
        if t == "end":
            if "next" in s:
                err(where, "`end` steps must not have `next`")
        elif not targets:
            err(where, "non-end step needs `next`")
        if t == "decision":
            if len(targets) < 2:
                err(where, "decision needs at least two `next` targets")
            seen_when: set[str] = set()
            for tid, when in targets:
                if blank(when):
                    err(where, f"decision target `{tid}` needs a `when`")
                    continue
                key = " ".join(when.split()).lower()
                if key in seen_when:
                    err(where, f"two exits share the condition `{when}` — the route is ambiguous")
                seen_when.add(key)
        if t == "handoff":
            if not isinstance(s.get("to"), str) or s["to"].count(".") != 1:
                err(where, "handoff needs `to: <workflow-id>.<step-id>`")
        elif "to" in s:
            err(where, "`to` is only allowed on handoff steps")

    if ids and not any("input" in s for s in ids.values()):
        err(rel, "no step has `input` — the PM has no way into this workflow")

    # graph rules
    if steps and isinstance(steps[0], dict) and steps[0].get("id") in ids:
        entry = steps[0]["id"]
        adj = {sid: [t for t, _ in targets_by_id.get(sid, [])] for sid in ids}
        for sid, outs in adj.items():
            for t in outs:
                if t not in ids:
                    err(f"{rel} step `{sid}`", f"next target `{t}` does not exist")
        # reachability from entry
        seen, stack = set(), [entry]
        while stack:
            n = stack.pop()
            if n in seen:
                continue
            seen.add(n)
            stack.extend(x for x in adj.get(n, []) if x in ids)
        for sid in ids:
            if sid not in seen:
                err(f"{rel} step `{sid}`", "not reachable from the entry step")
        # every non-end step can reach an end
        ends = {sid for sid, s in ids.items() if s.get("type") == "end"}
        if not ends:
            err(rel, "no `end` step")
        rev: dict[str, list[str]] = {sid: [] for sid in ids}
        for sid, outs in adj.items():
            for t in outs:
                if t in rev:
                    rev[t].append(sid)
        can_end, stack = set(), list(ends)
        while stack:
            n = stack.pop()
            if n in can_end:
                continue
            can_end.add(n)
            stack.extend(rev[n])
        for sid in ids:
            if sid not in can_end:
                err(f"{rel} step `{sid}`", "has no path to an end step")
    return data


def main() -> int:
    workflows: dict[str, dict] = {}
    files = sorted(WF_DIR.glob("*.yaml")) if WF_DIR.exists() else []
    for stray in (WF_DIR.iterdir() if WF_DIR.exists() else []):
        if stray.name != ".gitkeep" and stray.suffix != ".yaml":
            err(f"workflows/{stray.name}", "only `<id>.yaml` files belong here (rename .yml to .yaml)")
    for p in files:
        d = check_workflow(p)
        if d and isinstance(d.get("id"), str):
            workflows[d["id"]] = d

    # map.yaml
    m = load_yaml(MAP) if MAP.exists() else PARSE_ERROR
    if m is PARSE_ERROR:
        if not MAP.exists():
            err("map.yaml", "missing")
        listed: dict[str, str] = {}
    else:
        if not isinstance(m, dict):
            err("map.yaml", "top level must be a mapping with `entry`, `exit`, `groups`")
            m = {}
        extra = set(m) - MAP_ALLOWED
        if extra:
            err("map.yaml", f"unknown fields {sorted(extra)} — add to SCHEMA.md first")
        groups = m.get("groups")
        listed = {}
        if not isinstance(groups, list):
            err("map.yaml", "`groups` must be a list")
            groups = []
        group_ids: set[str] = set()
        for g in groups:
            gid = g.get("id") if isinstance(g, dict) else None
            where = f"map.yaml group `{gid}`"
            if not isinstance(g, dict):
                err("map.yaml", f"group must be a mapping with `id`, `name`, `workflows`: {g!r}")
                continue
            if not isinstance(gid, str) or not ID_RE.match(gid) or blank(g.get("name")):
                err(where, "group needs kebab-case `id` and a non-empty `name`")
            if gid in group_ids:
                err(where, "duplicate group id")
            group_ids.add(gid)
            g_extra = set(g) - GROUP_ALLOWED
            if g_extra:
                err(where, f"unknown group fields {sorted(g_extra)} — add to SCHEMA.md first")
            if not isinstance(g.get("workflows"), list):
                err(where, "`workflows` must be a list of workflow ids")
                continue
            for w in g["workflows"]:
                if not isinstance(w, str):
                    err(where, f"workflow entry must be an id string: {w!r}")
                    continue
                if w in listed:
                    err(where, f"workflow `{w}` listed in more than one group")
                listed[w] = gid
                if w not in workflows:
                    err(where, f"workflow `{w}` has no file workflows/{w}.yaml")
        for w in workflows:
            if w not in listed:
                err("map.yaml", f"workflow `{w}` exists but is not in any group")
        for key in ("entry", "exit"):
            ref = m.get(key)
            if not isinstance(ref, str) or ref.count(".") != 1:
                err("map.yaml", f"`{key}` must be `<workflow-id>.<step-id>`")
                continue
            tw, _, ts = ref.partition(".")
            if tw not in workflows:
                err("map.yaml", f"`{key}` names unknown workflow `{tw}`")
                continue
            wsteps = [x for x in workflows[tw].get("steps") or [] if isinstance(x, dict)]
            step = next((x for x in wsteps if x.get("id") == ts), None)
            if step is None:
                err("map.yaml", f"`{key}` names unknown step `{ref}`")
            elif key == "entry" and (step is not wsteps[0] or "input" not in step):
                err("map.yaml", f"`entry` must be the first step of `{tw}` and carry `input`")
            elif key == "exit" and step.get("type") != "end":
                err("map.yaml", f"`exit` must be an `end` step")

        # rule 8: every step of every workflow is reachable from the system entry, following
        # `next` inside a workflow and `handoff.to` across workflows. A step that is not is stale.
        entry_ref = m.get("entry")
        if isinstance(entry_ref, str) and entry_ref.count(".") == 1 and entry_ref.split(".")[0] in workflows:
            graph: dict[str, list[str]] = {}
            for wid, d in workflows.items():
                for st in d.get("steps") or []:
                    if not isinstance(st, dict) or not isinstance(st.get("id"), str):
                        continue
                    key = f"{wid}.{st['id']}"
                    outs = [f"{wid}.{t}" for t, _ in norm_next(st, "", report=False)]
                    if st.get("type") == "handoff" and isinstance(st.get("to"), str):
                        outs.append(st["to"])
                    graph[key] = outs
            seen_all, stack = set(), [entry_ref]
            while stack:
                n = stack.pop()
                if n in seen_all:
                    continue
                seen_all.add(n)
                stack.extend(x for x in graph.get(n, []) if x in graph)
            for key in graph:
                if key not in seen_all:
                    err("workflows/" + key.replace(".", ".yaml step `", 1) + "`", "not reachable from the system entry — a stale step")
            exit_ref = m.get("exit")
            if isinstance(exit_ref, str) and exit_ref in graph and exit_ref not in seen_all:
                err("map.yaml", "`exit` is not reachable from `entry`")

    # handoff targets across workflows
    for wid, d in workflows.items():
        for s in d.get("steps") or []:
            if isinstance(s, dict) and s.get("type") == "handoff" and isinstance(s.get("to"), str):
                tw, _, ts = s["to"].partition(".")
                where = f"workflows/{wid}.yaml step `{s.get('id')}`"
                if tw == wid:
                    err(where, "handoff to own workflow — use `next` instead")
                elif tw not in workflows:
                    err(where, f"handoff target workflow `{tw}` does not exist")
                else:
                    tids = {x.get("id") for x in workflows[tw].get("steps") or [] if isinstance(x, dict)}
                    if ts not in tids:
                        err(where, f"handoff target step `{ts}` not in `{tw}`")

    if errors:
        print(f"FAIL — {len(errors)} problem(s):")
        for e in errors:
            print("  -", e)
        return 1
    print(f"OK — {len(workflows)} workflow(s), map consistent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
