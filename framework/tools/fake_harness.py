#!/usr/bin/env python3
"""A stand-in harness for tests of framework/tools/run.py (`--harness fake`).

Reads the runner's prompt from argv (or stdin), finds the record path and the
legal exits in it, writes a minimal but valid output block for the step into
the record, and runs the `advance` call the contract asks for:
  challenger steps  a `## Findings — <step>` block with one finding
  deliver.plan      a plan section and a task list (T001 [P] [node] grammar)
  deliver.execute   the task list with every task ticked
  deliver.verify    the findings block plus a "verified" line under `## Verification`
  every other step  one line under `## <step>`
A reviewer prompt ("Do not call advance") only appends a finding.

The exit taken is the first legal exit, except at the decisions where the
first exit leaves the happy path (HAPPY below: sort → discuss, tasks-done →
verify, passes → accept, was-rule → done, ...), so a run walks a record from
define.sort to deliver.done through every PM stop. `--when` is passed as the
same number as `--to` where the exit has a condition; `--answer` is never
passed: a PM step is never reached by the fake (the runner stops first).

For tests of the runner's retry: FAKE_HARNESS_STALL=<step ref> makes the fake
do nothing the first time it is asked for that step (a marker file under
changes/ remembers it); FAKE_HARNESS_STALL=always makes it never move.
For tests of the runner's move check: FAKE_HARNESS_OVERSTEP=<step ref> makes
the fake, after its own advance at that step, answer the PM step it landed on
itself (`advance --to 1 --answer fake`), which the runner must refuse.
"""
from __future__ import annotations
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()
PY = sys.executable or "python3"
HAPPY = {
    "define.sort": "discuss",
    "define.settled": "answered",
    "deliver.tasks-done": "verify",
    "deliver.passes": "accept",
    "deliver.was-rule": "done",
    "deliver.was-rule-drop": "dropped",
    "foundation.new-or-change": "architecture",
    "foundation.foundation-only": "done",
}
EXIT_RE = re.compile(r"^\s*(\d+)\. (\S+)(?:\s+when: (.*))?$")


def parse(prompt: str):
    record = re.search(r"^Record: (.+)$", prompt, re.M)
    step = re.search(r"^(\S+\.\S+) — .*\(lane: ", prompt, re.M)
    exits = []
    in_exits = False
    for line in prompt.splitlines():
        if line.startswith("Legal exits"):
            in_exits = True
            continue
        m = EXIT_RE.match(line) if in_exits else None
        if m:
            exits.append((int(m.group(1)), m.group(2), m.group(3)))
        elif in_exits and line.strip() == "":
            in_exits = False
    return (record.group(1).strip() if record else None), (step.group(1) if step else None), exits


def block(step: str, mode_challenger: bool, reviewer: str = None) -> tuple[str, str]:
    """(heading, body) to write for this step."""
    if mode_challenger:
        who = reviewer or "fake"
        return f"## Findings — {step}", f"- [{who}] one finding, fixed: a wording made precise\n"
    if step == "deliver.plan":
        return "## Plan", ("What changes for the user: the fake plan. What will not change: everything else.\n\n"
                          "## Tasks\n- [ ] T001 [P] [login] write the component, in code/backend/auth/auth.py\n"
                          "- [ ] T002 [login] write its test, in code/backend/auth/test_auth.py\n")
    if step == "deliver.execute":
        return "## Tasks (executed)", "- [x] T001 [P] [login] write the component, in code/backend/auth/auth.py\n- [x] T002 [login] write its test\n"
    return f"## {step}", f"done by the fake harness: {step}\n"


def append(record: Path, heading: str, body: str) -> None:
    text = record.read_text(encoding="utf-8")
    if heading in text and heading.startswith("## Findings"):
        # a further reviewer: add its line inside the existing block
        head, _, rest = text.partition(heading + "\n")
        nxt = re.search(r"^## ", rest, re.M)
        blk, tail = (rest[:nxt.start()], rest[nxt.start():]) if nxt else (rest, "")
        text = head + heading + "\n" + blk.rstrip("\n") + "\n" + body + "\n" + tail
    else:
        text = text.rstrip("\n") + f"\n\n{heading}\n\n{body}"
    record.write_text(text, encoding="utf-8")


def stalled(step: str) -> bool:
    cfg = os.environ.get("FAKE_HARNESS_STALL", "")
    if not cfg:
        return False
    if cfg == "always":
        return True
    if cfg != step:
        return False
    marker = ROOT / "changes" / f".fake-stall-{step}"
    if marker.exists():
        return False
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("stalled once\n", encoding="utf-8")
    return True


def main() -> int:
    prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else sys.stdin.read()
    record, step, exits = parse(prompt)
    if not record or not step:
        print("fake harness: no record or step in the prompt")
        return 1
    if stalled(step):
        print(f"fake harness: stalling at {step} (FAKE_HARNESS_STALL)")
        return 0
    rec = ROOT / record
    challenger = "Mode: challenger" in prompt
    reviewer = re.search(r"reviewer pass `([^`]+)`", prompt)
    heading, body = block(step, challenger, reviewer.group(1) if reviewer else None)
    append(rec, heading, body)
    print(f"fake harness: wrote `{heading}` into {record}")
    if "Do not call advance" in prompt:
        print("fake harness: reviewer pass, no advance")
        return 0
    if step == "deliver.verify":
        append(rec, "## Verification", "verified: whole suite run, every criterion holds (fake)\n")
    if not exits:
        print("fake harness: no legal exits in the prompt")
        return 1
    want = HAPPY.get(step)
    chosen = next((e for e in exits if want and e[1].partition(".")[2] == want), exits[0])
    argv = [PY, "framework/tools/orchestrate.py", "advance", record, "--to", str(chosen[0])]
    if chosen[2]:
        argv += ["--when", str(chosen[0])]
    r = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
    print(f"fake harness: {' '.join(argv[1:])}")
    print(r.stdout + r.stderr)
    if r.returncode == 0 and os.environ.get("FAKE_HARNESS_OVERSTEP") == step:
        base = [PY, "framework/tools/orchestrate.py", "advance", record, "--to", "1", "--answer", "fake"]
        r2 = subprocess.run(base + ["--when", "1"], cwd=ROOT, capture_output=True, text=True)
        if r2.returncode != 0:
            r2 = subprocess.run(base, cwd=ROOT, capture_output=True, text=True)
        print("fake harness: OVERSTEP, answered the next step itself\n" + r2.stdout + r2.stderr)
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
