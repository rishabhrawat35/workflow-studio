#!/usr/bin/env python3
"""Export a change record's task list to GitHub issues (`/speckit-taskstoissues`).

Usage (from the product repository root, with framework/ copied in):
  tasks_to_issues.py <changes/record.md> [--repo owner/name] [--dry-run]

The record's AI section holds the task list, one line per task in the
plan's grammar:  - [ ] T001 [P] [node-id] what, in which file
This tool creates one GitHub issue per task with `gh issue create`
(title = task id + text; body = node ids, record path, lane; label
`workflow-studio`) and writes the issue number back onto the task line as
` → #123`. A task line that already carries ` → #…` is skipped, so the
tool can be rerun after a re-plan and only the new tasks are exported.

The record stays the source of truth: the issues are a mirror for people
who live in GitHub, nothing is imported back, and no state moves here.
Allowed only once the plan is approved: the record must be at
`deliver.execute` or a later Deliver step (tasks-done, verify, passes,
accept, commit, was-rule, resume-define, done). A record back at
`deliver.plan` is not approved and is refused.

`--dry-run` prints what would be created and writes nothing; it is the
default when `gh` is not installed. Exit code 1 on any refusal.
"""
import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # no __pycache__ in the product repository
sys.path.insert(0, str(Path(__file__).resolve().parent))
from orchestrate import Refused, read_record, write_record  # noqa: E402  (the record parser is shared, not copied)

ROOT = Path.cwd()
LABEL = "workflow-studio"
ALLOWED_STEPS = ("deliver.execute", "deliver.tasks-done", "deliver.verify", "deliver.passes", "deliver.accept",
                 "deliver.commit", "deliver.was-rule", "deliver.resume-define", "deliver.done")
# - [ ] T001 [P] [node-a] [node-b] text   → #12     (or → <issue url>, when gh printed no number)
TASK = re.compile(r"^(?P<indent>\s*)- \[(?P<tick>[ xX])\] (?P<id>T\d{3,})\s+(?P<tags>(?:\[[^\]\s]+\]\s*)*)(?P<text>.*?)(?P<issue>\s+→\s+(?:#\S+|https?://\S+).*)?\s*$")
NODE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def parse_tasks(body: str):
    """Yield (line_no, task) for every task line; task = id, tick, nodes, text, issue (or None)."""
    for i, line in enumerate(body.splitlines()):
        m = TASK.match(line)
        if not m:
            continue
        tags = re.findall(r"\[([^\]\s]+)\]", m.group("tags"))
        yield i, {"id": m.group("id"), "done": m.group("tick") != " ", "parallel": "P" in tags,
                  "nodes": [t for t in tags if t != "P" and NODE.match(t)], "text": m.group("text").strip(),
                  "issue": (m.group("issue") or "").strip().lstrip("→ ").strip() or None}


def issue_body(task, record: Path, lane: str) -> str:
    lines = [f"Task {task['id']} of change record `{record.as_posix()}` (lane: {lane}).", ""]
    lines.append("Nodes: " + (", ".join(f"`{n}`" for n in task["nodes"]) if task["nodes"] else "none named"))
    if task["parallel"]:
        lines.append("Marked [P]: touches different files from every unfinished task and can run alongside them.")
    lines += ["", "The change record is the source of truth; this issue mirrors one task line of it. Nothing is imported back."]
    return "\n".join(lines)


def gh_create(task, record, lane, repo):
    cmd = ["gh", "issue", "create", "--title", f"{task['id']} {task['text']}", "--body", issue_body(task, record, lane), "--label", LABEL]
    if repo:
        cmd += ["--repo", repo]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        return None, (r.stderr or r.stdout).strip()
    url = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""
    m = re.search(r"/issues/(\d+)\s*$", url)
    return (f"#{m.group(1)}" if m else url), None


def ensure_label(repo):
    cmd = ["gh", "label", "create", LABEL, "--description", "task exported from a change record", "--force"]
    if repo:
        cmd += ["--repo", repo]
    subprocess.run(cmd, capture_output=True, text=True)  # best effort; a failure surfaces at issue create


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("record")
    ap.add_argument("--repo", help="owner/name; default: the repository gh infers from the git remote")
    ap.add_argument("--dry-run", action="store_true", help="print what would be created; default when gh is missing")
    a = ap.parse_args()
    path = Path(a.record)
    if not path.exists():
        print(f"refused: {path} does not exist")
        return 1
    meta, body = read_record(path)
    step = meta.get("step")
    if step not in ALLOWED_STEPS:
        print(f"refused: the record is at {step or 'no state'}; tasks are exported only once the plan is approved "
              f"(deliver.execute or later). Move it with orchestrate.py; never by hand.")
        return 1
    tasks = list(parse_tasks(body))
    if not tasks:
        print("refused: no task lines of the form `- [ ] T001 [P] [node-id] …` in the record")
        return 1
    dry = a.dry_run
    if not dry and not shutil.which("gh"):
        print("gh is not installed: running as --dry-run")
        dry = True
    lane = str(meta.get("lane", "full"))
    rel = path.resolve().relative_to(ROOT) if path.resolve().is_relative_to(ROOT) else path
    lines = body.splitlines()
    created, skipped, failed = 0, 0, 0
    if not dry:
        ensure_label(a.repo)
    for i, t in tasks:
        if t["issue"]:
            print(f"skip    {t['id']}  already exported {t['issue']}")
            skipped += 1
            continue
        if dry:
            print(f"would create  {t['id']} {t['text']}  [nodes: {', '.join(t['nodes']) or '-'}; label {LABEL}"
                  + (f"; repo {a.repo}" if a.repo else "") + "]")
            created += 1
            continue
        ref, err = gh_create(t, rel, lane, a.repo)
        if err:
            print(f"FAILED  {t['id']}: {err}")
            failed += 1
            continue
        lines[i] = lines[i].rstrip() + f" → {ref}"
        write_record(path, meta, "\n".join(lines) + ("\n" if body.endswith("\n") else ""))
        body = "\n".join(lines) + ("\n" if body.endswith("\n") else "")
        print(f"created {t['id']} → {ref}")
        created += 1
    print(f"{'dry run: ' if dry else ''}{created} issue(s) {'would be ' if dry else ''}created, {skipped} skipped, {failed} failed"
          + ("" if dry else f"; the record now carries the issue numbers ({rel.as_posix()})"))
    return 1 if failed else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Refused as e:
        print(f"refused: {e}")
        sys.exit(1)
    except BrokenPipeError:
        sys.exit(0)
