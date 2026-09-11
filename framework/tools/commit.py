#!/usr/bin/env python3
"""The one code commit of `deliver.commit` (`/speckit-git-commit`).

Usage (from the product repository root, with framework/ copied in):
  commit.py <changes/record.md> [--dry-run] [--still-needs-logic]

Allowed only when the record is at `deliver.commit`, i.e. the PM has
answered "accepted" at `deliver.accept`. Nothing is committed by hand and
nothing is committed earlier. What the commit does, in order:

  1. refuses if not inside a git repository, if the record is not at
     `deliver.commit`, or if the git index already holds changes that are
     not part of this delivery (stage nothing by hand; the tool stages);
  2. regenerates the indexes (`logic_index.py`, `components_index.py`,
     `decisions_index.py`); the decision log must validate or nothing happens;
  3. sets each delivered node's `Status:` line to `delivered <version>`
     (the version is the node file's last commit, the save `define.commit`
     made) and writes the outcome into the record;
  4. moves the record through `orchestrate.py advance`: commit → was-rule →
     done (or → resume-define with `--still-needs-logic`, for a rule whose
     request continues in Define);
  5. stages exactly: the code and test files the record's task lines name
     (each named file's component folder, so its tests beside it come
     along), the delivered node files, the decision files written under
     this record (and existing ones that gained `superseded_by`), the three
     indexes, the record, `changes/QUEUE.md` and `architecture.md` when
     modified (a delivered rule), and commits with the message
     `<record slug>: <title>` and a body listing nodes and decision ids.

`--dry-run` does the refusal checks, then prints the file set and the
message and changes nothing. Exit code 1 on any refusal. If the commit
fails after the record was moved (a git hook, a refusal from
`orchestrate.py`), the record and the node files are restored and the index
is unstaged, so the record is still at `deliver.commit` and the tool can be
run again. Changed code files that no task line names are reported and left
uncommitted, never staged.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # no __pycache__ in the product repository
sys.path.insert(0, str(Path(__file__).resolve().parent))
from orchestrate import Refused, read_record, write_record  # noqa: E402
from tasks_to_issues import parse_tasks  # noqa: E402

ROOT = Path.cwd()
TOOLS = Path(__file__).resolve().parent
STEP = "deliver.commit"
PATH_IN_TEXT = re.compile(r"(?<![\w/])(?:code|tests?)/[\w.\-/]+")
INDEXES = ["logic/INDEX.md", "code/COMPONENTS.md", "decisions/INDEX.md"]


def git(*args, check=True):
    r = subprocess.run(["git", *args], capture_output=True, text=True, cwd=ROOT)
    if check and r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout).strip())
    return r.stdout


def run_tool(name: str) -> tuple[int, str]:
    r = subprocess.run([sys.executable, str(TOOLS / name)], capture_output=True, text=True, cwd=ROOT)
    return r.returncode, (r.stdout + r.stderr).strip()


def component_dir(p: Path):
    """code/<system>/<component>/ for a file under it; the path itself otherwise."""
    parts = p.parts
    if len(parts) >= 3 and parts[0] == "code":
        return Path(*parts[:3])
    return p


def title_of(body: str, stem: str) -> str:
    return next((l[2:].strip() for l in body.splitlines() if l.startswith("# ")), stem)


def slug_of(stem: str) -> str:
    """<date>-<n>-<slug> (a request) or <date>-<n>.<chunk>-<slug> (a child of a broken-down request) → <slug>."""
    return re.sub(r"^\d{4}-\d{2}-\d{2}-\d+(?:\.\d+)?-", "", stem)


def worktree_changes():
    """{path: XY} from `git status --porcelain` (renames reduced to the new path)."""
    out = {}
    for line in git("status", "--porcelain", "-z", "--untracked-files=all").split("\0"):
        if not line.strip():
            continue
        code, p = line[:2], line[3:]
        out[p] = code
    return out


def collect(meta, body, record_rel: Path):
    tasks = [t for _, t in parse_tasks(body)]
    nodes = sorted({n for t in tasks for n in t["nodes"]})
    files, missing = set(), []
    for t in tasks:  # only the task lines: a path in the trace or plan prose is not part of the delivery
        for m in PATH_IN_TEXT.finditer(t["text"]):
            p = Path(m.group(0).rstrip(".,;:"))
            if (ROOT / p).exists():
                files.add(component_dir(p).as_posix())
            else:
                missing.append(f"{t['id']}: {p.as_posix()}")
    node_files = {}
    for n in nodes:
        hits = [p for p in (ROOT / "logic").rglob(f"{n}.md")] if (ROOT / "logic").exists() else []
        if hits:
            node_files[n] = hits[0].relative_to(ROOT)
    changes = worktree_changes()
    decisions = []
    for p in sorted((ROOT / "decisions").glob("D-*.md")) if (ROOT / "decisions").exists() else []:
        rel = p.relative_to(ROOT).as_posix()
        dmeta, _ = read_record(p)
        if str(dmeta.get("record", "")) == record_rel.as_posix() or changes.get(rel, "").strip() in ("M", "MM"):
            decisions.append(rel)
    extra = [f for f in ("changes/QUEUE.md", "architecture.md") if f in changes]
    return tasks, nodes, files, node_files, decisions, extra, changes, missing


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("record")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--still-needs-logic", action="store_true", help="was-rule: the request continues in Define (resume-define) instead of done")
    a = ap.parse_args()
    path = Path(a.record)
    # 1. refusals
    r = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, cwd=ROOT)
    if r.returncode != 0 or Path(r.stdout.strip()).resolve() != ROOT.resolve():
        print("refused: run from the root of the product's git repository")
        return 1
    if not path.exists():
        print(f"refused: {path} does not exist")
        return 1
    meta, body = read_record(path)
    if meta.get("step") != STEP:
        print(f"refused: the record is at {meta.get('step') or 'no state'}, not {STEP}; the commit happens only after the PM accepts at deliver.accept")
        return 1
    record_rel = path.resolve().relative_to(ROOT.resolve())
    tasks, nodes, files, node_files, decisions, extra, changes, missing = collect(meta, body, record_rel)
    if not tasks:
        print("refused: the record has no task list (`- [ ] T001 [P] [node-id] …`); nothing to commit")
        return 1
    if any(not t["done"] for t in tasks):
        print("note: unticked tasks in the record (a superseded plan?): " + ", ".join(t["id"] for t in tasks if not t["done"]))
    if missing:
        print("note: task lines name paths that do not exist (not staged): " + "; ".join(missing))
    planned = set(files) | {p.as_posix() for p in node_files.values()} | set(decisions) | set(extra) | set(INDEXES) | {record_rel.as_posix()}
    in_plan = lambda f: any(f == p or f.startswith(p.rstrip("/") + "/") for p in planned)  # noqa: E731
    outside = sorted(f for f in changes if f.startswith("code/") and not in_plan(f))
    if outside:
        print("note: changed code files no task line names; they stay uncommitted (a task that touched them should name them): " + ", ".join(outside))
    staged = [l for l in git("diff", "--cached", "--name-only").splitlines() if l.strip()]
    unrelated = [s for s in staged if not in_plan(s)]
    if unrelated:
        print("refused: the git index already holds changes outside this delivery; unstage them first: " + ", ".join(unrelated))
        return 1
    ids = [Path(d).name[:6] for d in decisions]
    title = title_of(body, path.stem)
    message = f"{slug_of(path.stem)}: {title}\n\nRecord: {record_rel.as_posix()}\nNodes: {', '.join(nodes) or 'none'}\nDecisions: {', '.join(ids) or 'none'}\n"
    if a.dry_run:
        print("dry run — would stage:")
        for p in sorted(planned):
            print("  ", p, "(missing)" if not (ROOT / p).exists() and p not in INDEXES else "")
        print("would regenerate:", ", ".join(INDEXES))
        print(f"would advance: {STEP} → deliver.was-rule → {'deliver.resume-define' if a.still_needs_logic else 'deliver.done'}")
        print("commit message:\n" + "\n".join("  " + l for l in message.splitlines()))
        return 0
    # 2. indexes
    for tool, folder in (("logic_index.py", "logic"), ("components_index.py", "code"), ("decisions_index.py", "decisions")):
        if not (ROOT / folder).exists():
            print(f"skip {tool}: no {folder}/ folder")
            continue
        rc, out = run_tool(tool)
        if rc != 0:
            print(f"refused: {tool} failed; the commit does not happen until it passes:\n{out}")
            return 1
        print(f"{tool}: ok")
    # 3. node status and outcome — snapshot first, so a failure later (orchestrate refusal, git hook) restores them
    before = {p: (ROOT / p).read_text(encoding="utf-8") for p in [record_rel.as_posix()] + [r.as_posix() for r in node_files.values()]}

    def roll_back(why: str) -> int:
        for p, text in before.items():
            (ROOT / p).write_text(text, encoding="utf-8")
        git("reset", "-q", "--", *sorted(planned), check=False)
        print(f"refused: {why}\nnothing committed; the record and the node files are as they were (still at {STEP}); the indexes were regenerated")
        return 1

    versions = {}
    for n, rel in node_files.items():
        sha = git("log", "-n1", "--format=%h", "--", rel.as_posix()).strip() or "unversioned"
        versions[n] = sha
        text = (ROOT / rel).read_text(encoding="utf-8")
        new = re.sub(r"^Status:.*$", f"Status: delivered {sha}", text, count=1, flags=re.M) if re.search(r"^Status:", text, re.M) \
            else text.rstrip("\n") + f"\n\nStatus: delivered {sha}\n"
        (ROOT / rel).write_text(new, encoding="utf-8")
    if not re.search(r"^## Outcome\s*$", body, re.M):
        body = body.rstrip("\n") + "\n\n## Outcome\n\ndelivered" + (": " + ", ".join(f"{n} @ {v}" for n, v in versions.items()) if versions else "") + "\n"
        write_record(path, meta, body)
    # 4. advance
    orch = [sys.executable, str(TOOLS / "orchestrate.py"), "advance", str(path)]
    for args in ([["--to", "deliver.was-rule"]] + ([["--to", "deliver.resume-define", "--when", "1"]] if a.still_needs_logic else [["--to", "deliver.done", "--when", "2"]])):
        r = subprocess.run(orch + args, capture_output=True, text=True, cwd=ROOT)
        print(r.stdout.splitlines()[0] if r.stdout else r.stderr.strip())
        if r.returncode != 0:
            return roll_back("orchestrate.py did not move the record:\n" + (r.stdout + r.stderr).strip())
    # 5. stage and commit
    to_add = [p for p in sorted(planned) if (ROOT / p).exists()]
    try:
        git("add", "--", *to_add)
        git("commit", "-q", "-m", message)
    except RuntimeError as e:
        return roll_back(f"git: {e}")
    sha = git("rev-parse", "--short", "HEAD").strip()
    print(f"committed {sha}: {message.splitlines()[0]}")
    print("files: " + ", ".join(to_add))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except RuntimeError as e:
        print(f"refused: git: {e}")
        sys.exit(1)
    except Refused as e:
        print(f"refused: {e}")
        sys.exit(1)
    except BrokenPipeError:
        sys.exit(0)
