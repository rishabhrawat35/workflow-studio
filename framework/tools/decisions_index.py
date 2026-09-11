#!/usr/bin/env python3
"""Generate decisions/INDEX.md for a product repository and validate the decision log.

Run from the product repository root:  python3 <path-to>/decisions_index.py
Files: decisions/D-<nnnn>-<slug>.md — YAML front matter + body
(format in framework/components/decision-log.md). The id is the filename's
D-<nnnn> part. Validates the log as a contract and exits 1 on any finding:
required fields; category from the list; made_at with time and offset;
supersedes / superseded_by pointing back at each other; Reasons naming a
rejected alternative ("Instead of …"); resources present for AI decisions;
no empty section; and, when git is present, no change to an existing
decision file except adding `superseded_by`.
"""
from __future__ import annotations
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path.cwd()
DEC = ROOT / "decisions"
OUT = DEC / "INDEX.md"
CATEGORIES = ["product", "business", "ui", "frontend", "backend", "code", "infra", "software", "process"]
REQUIRED = ["made_at", "category", "made_by", "at_step"]
ALLOWED = set(REQUIRED) | {"region", "effective_from", "record", "nodes", "resources", "supersedes", "superseded_by", "links"}
FM = re.compile(r"^---\s*\n(.*?)\n---\s*(?:\n(.*))?$", re.S)
ID_RE = re.compile(r"^D-\d{4}$")
FILE_RE = re.compile(r"^(D-\d{4})-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")


def parse_when(v):
    """Return an aware datetime or None. YAML may hand us a str, date or datetime."""
    try:
        dt = datetime.fromisoformat(str(v).replace(" ", "T"))
    except ValueError:
        return None
    return dt if dt.tzinfo and "T" in str(v).replace(" ", "T") else None


def section(body: str, name: str) -> str:
    m = re.search(rf"^## {re.escape(name)}\s*$(.*?)(?=^## |\Z)", body, re.M | re.S)
    return m.group(1).strip() if m else ""


def git_immutability_findings() -> list[str]:
    """Existing decision files may only gain a `superseded_by:` line."""
    if not (ROOT / ".git").exists():
        return []
    out = []
    try:
        status = subprocess.run(["git", "diff", "--name-status", "HEAD", "--", "decisions/"], capture_output=True, text=True, cwd=ROOT).stdout
    except OSError:
        return []
    for line in status.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        kind, path = parts[0][0], parts[-1]
        if path.endswith("INDEX.md"):
            continue
        if kind == "D":
            out.append(f"{path}: deleted — decisions are never deleted")
        elif kind == "M":
            diff = subprocess.run(["git", "diff", "--unified=0", "HEAD", "--", path], capture_output=True, text=True, cwd=ROOT).stdout
            changed = [l for l in diff.splitlines() if (l.startswith("+") or l.startswith("-")) and not l.startswith(("+++", "---"))]
            if any(l.startswith("-") for l in changed) or any(not l.startswith("+superseded_by:") for l in changed):
                out.append(f"{path}: edited — an existing decision may only gain a `superseded_by:` line")
    return out


def main() -> int:
    if not DEC.exists():
        print("no decisions/ folder here; run from the product repository root")
        return 1
    findings, decisions = [], {}
    for p in sorted(x for x in DEC.glob("*.md") if x.name != "INDEX.md"):
        fm = FILE_RE.match(p.name)
        if not fm:
            findings.append(f"{p.name}: filename must be D-<nnnn>-<slug>.md")
            continue
        did = fm.group(1)
        try:
            text = p.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            findings.append(f"{p.name}: not valid UTF-8 text")
            continue
        m = FM.match(text.replace("\r\n", "\n"))
        if not m:
            findings.append(f"{p.name}: no YAML front matter")
            continue
        try:
            meta = yaml.safe_load(m.group(1)) or {}
        except yaml.YAMLError as e:
            findings.append(f"{p.name}: front matter parse error: {e}")
            continue
        if not isinstance(meta, dict):
            findings.append(f"{p.name}: front matter must be a mapping of fields")
            continue
        body = (m.group(2) or "").strip()
        title = next((l[2:].strip() for l in body.splitlines() if l.startswith("# ")), "")
        for k in REQUIRED:
            if k not in meta or meta[k] in (None, ""):
                findings.append(f"{p.name}: missing `{k}`")
        for k in set(meta) - ALLOWED:
            findings.append(f"{p.name}: unknown field `{k}`")
        for k in ("nodes", "resources", "links"):
            if k in meta and not (isinstance(meta[k], list) and all(isinstance(x, str) for x in meta[k])):
                findings.append(f"{p.name}: `{k}` must be a list of strings, e.g. [refund-request]")
                meta[k] = []
        for k in ("category", "made_by", "at_step", "region", "record"):
            if k in meta and not isinstance(meta[k], str):
                findings.append(f"{p.name}: `{k}` must be a string")
                meta[k] = str(meta[k])
        when = parse_when(meta.get("made_at")) if meta.get("made_at") else None
        if meta.get("made_at") and when is None:
            findings.append(f"{p.name}: made_at must be a quoted ISO timestamp with time and offset, e.g. \"2026-09-09T14:32+05:30\"")
        if meta.get("category") not in CATEGORIES:
            findings.append(f"{p.name}: category `{meta.get('category')}` not in {CATEGORIES}")
        if meta.get("made_by") not in ("PM", "AI"):
            findings.append(f"{p.name}: made_by must be PM or AI")
        if meta.get("made_by") == "AI" and not meta.get("resources"):
            findings.append(f"{p.name}: an AI decision must name `resources` (the component or folder it governs)")
        for k in ("supersedes", "superseded_by"):
            if k in meta and not (isinstance(meta[k], str) and ID_RE.match(meta[k])):
                findings.append(f"{p.name}: `{k}` must be an id like D-0042")
        if "status" in meta:
            findings.append(f"{p.name}: `status` is derived (active unless superseded_by is set); remove it")
        if not title:
            findings.append(f"{p.name}: body must start with `# <one-line decision>`")
        for name in ("Situation", "Decision", "Reasons"):
            if not section(body, name):
                findings.append(f"{p.name}: section `## {name}` missing or empty")
        if section(body, "Reasons") and not re.search(r"^\s*(?:[-*]\s*)?Instead of\b", section(body, "Reasons"), re.M | re.I):
            findings.append(f"{p.name}: Reasons must name a rejected alternative on a line starting \"Instead of\"; no alternative, no decision file")
        if did in decisions:
            findings.append(f"{p.name}: duplicate id {did} (also {decisions[did]['file']})")
        decisions[did] = {"file": p.name, "meta": meta, "title": title, "when": when}

    for did, d in decisions.items():
        m = d["meta"]
        sup = m.get("supersedes")
        if isinstance(sup, str) and ID_RE.match(sup):
            if sup not in decisions:
                findings.append(f"{d['file']}: supersedes unknown decision {sup}")
            elif decisions[sup]["meta"].get("superseded_by") != did:
                findings.append(f"{decisions[sup]['file']}: must carry `superseded_by: {did}`")
        by = m.get("superseded_by")
        if isinstance(by, str) and ID_RE.match(by):
            if by not in decisions:
                findings.append(f"{d['file']}: superseded_by unknown decision {by}")
            elif decisions[by]["meta"].get("supersedes") != did:
                findings.append(f"{decisions[by]['file']}: must carry `supersedes: {did}` to match {d['file']}")
    findings += git_immutability_findings()

    lines = ["# Decisions", "", "Generated by framework/tools/decisions_index.py. Do not edit by hand.",
             "Active decisions by category, newest first; then the supersede chains. A decision is active unless `superseded_by` is set.", ""]
    for cat in CATEGORIES:
        rows = [d for d in decisions.values() if d["meta"].get("category") == cat and not d["meta"].get("superseded_by")]
        if not rows:
            continue
        lines += [f"## {cat}", ""]
        for d in sorted(rows, key=lambda x: x["when"].timestamp() if x["when"] else 0, reverse=True):
            m = d["meta"]
            nodes = ", ".join(f"`{n}`" for n in (m.get("nodes") or [])) or "—"
            region = f" · {m['region']}" if m.get("region") else ""
            lines.append(f"- **{d['file'].split('-')[0]}-{d['file'].split('-')[1]}** {d['title']} — {m.get('made_at')}{region} · {m.get('made_by')} at `{m.get('at_step')}` · nodes {nodes} · [{d['file']}]({d['file']})")
        lines.append("")
    chains = [(did, d) for did, d in decisions.items() if d["meta"].get("supersedes")]
    if chains:
        lines += ["## Supersede chains", ""] + [f"- {d['meta']['supersedes']} → **{did}** ({d['title']})" for did, d in chains] + [""]
    if findings:
        lines += ["## Findings (the log is a contract; fix these)", ""] + [f"- {f}" for f in findings]
    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(decisions)} decisions, {len(findings)} finding(s))")
    for f in findings:
        print("  -", f)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
