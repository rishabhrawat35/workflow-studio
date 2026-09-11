#!/usr/bin/env python3
"""A stand-in harness for tests of framework/tools/run.py (`--harness fake`).

Reads the runner's prompt from argv (or stdin), finds the record path and the
legal exits in it, writes a minimal but valid output block for the step into
the record, and runs the `advance` call the contract asks for:
  challenger steps  a `## Findings — <step>` block with one finding; at
                    define.challenge on a record that carries an `## Impact —
                    proposed` block, one more finding per `@node` tag under
                    code/ that the block's dependants omit (E20)
  define.breakdown  a `## Breakdown — proposed <date>` block (PLAN §3.3): three
                    chunks named after the record's slug, chunk 3 depending on
                    chunk 1, each naming its own node in backticks; on a record
                    that carries an impact block, two chunks: the replacement
                    chunk before the removal chunk (E16); a rewrite after a PM
                    answer appends a new block, never edits the old one
  define.impact     an `## Impact — proposed <date>` block (PLAN §3.4): the node
                    removed (the first backticked id after "remove" in the
                    record, else the record's slug), the dependants read from
                    the `@node` tags under code/ (never guessed), each with what
                    stops working, the four options and one recommendation; one
                    stored-data line, "keep" recommended
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
passed: a PM step is never reached by the fake (the runner stops first), and
the fake never answers a gate — define.confirm-breakdown and
define.confirm-impact included.

Outside the runner, `fake_harness.py --discuss <record>` writes the discussion
notes a PM step would leave (`## define.discuss`) and does not advance: on a
child record the notes are a proposed correction of the breakdown in the
PLAN §3.3 format — the parent's current chunks, minus the dropped ones, plus
one new chunk — so a `revise-breakdown` from that child reopens the parent
with a proposal `spawn` can consume (E4); on any other record, one line.

For tests of the runner's retry: FAKE_HARNESS_STALL=<step ref> makes the fake
do nothing the first time it is asked for that step (a marker file under
changes/ remembers it); FAKE_HARNESS_STALL=always makes it never move.
For tests of the runner's move check: FAKE_HARNESS_OVERSTEP=<step ref> makes
the fake, after its own advance at that step, answer the PM step it landed on
itself (`advance --to 1 --answer fake`), which the runner must refuse.
For tests of the runner's run.md: FAKE_HARNESS_SHOW_RUNMD=1 makes the fake print
changes/runs/<record-stem>/run.md as it stands while the fake runs (so the step
log shows what a second terminal would have seen mid-run).
For tests of spawn's refusals: FAKE_HARNESS_E5=1 makes the breakdown's chunks 2
and 3 name the same node with no dependency between them (E5).
For tests of the impact step: FAKE_HARNESS_NO_DEPENDANTS=1 makes the impact
block list no dependants, which `advance` refuses (E15: no impact stop).
"""
from __future__ import annotations
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.dont_write_bytecode = True  # no __pycache__ in the product repository

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
TAG_RE = re.compile(r"@node\s+([A-Za-z0-9][\w-]*)")
HEADING_RE = re.compile(r"^## (.+?)\s*$", re.M)


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


# ---------------------------------------------------------------- what the fake reads
def slug_of(stem: str) -> str:
    """<date>-<n>-<slug> or <date>-<n>.<chunk>-<slug> → <slug>."""
    return re.sub(r"^\d{4}-\d{2}-\d{2}-\d+(?:\.\d+)?-", "", stem)


def front_matter(text: str) -> dict:
    """The few front-matter fields the fake reads (parent, chunk), without PyYAML."""
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    out = {}
    for line in (m.group(1) if m else "").splitlines():
        k, sep, v = line.partition(":")
        if sep and not line.startswith((" ", "-")):
            out[k.strip()] = v.strip()
    return out


def sections(text: str):
    """[(title, body)] for every `## ` heading."""
    heads = list(HEADING_RE.finditer(text))
    return [(h.group(1), text[h.end():(heads[i + 1].start() if i + 1 < len(heads) else len(text))]) for i, h in enumerate(heads)]


def last_section(text: str, prefix: str):
    """(index, body) of the last `## <prefix>…` section, or (None, None)."""
    hit = (None, None)
    for i, (title, body) in enumerate(sections(text)):
        if title.casefold().startswith(prefix.casefold()):
            hit = (i, body)
    return hit


def tags_in_code() -> dict:
    """{node id: first file carrying its @node tag} for every tag under code/."""
    out = {}
    d = ROOT / "code"
    if not d.exists():
        return out
    for p in sorted(x for x in d.rglob("*") if x.is_file() and x.suffix in (".py", ".js", ".ts", ".go", ".rs", ".java", ".rb", ".md", ".txt")):
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in TAG_RE.finditer(text):
            out.setdefault(m.group(1).casefold(), p.relative_to(ROOT).as_posix())
    return out


def removed_node(text: str, stem: str) -> str:
    """The node a removal names: the first backticked id after "remove"/"removing"/"retire", else the record's slug."""
    m = re.search(r"remov\w*|retir\w*", text, re.I)
    if m:
        b = re.search(r"`([A-Za-z0-9][\w-]*)`", text[m.end():])
        if b:
            return b.group(1).casefold()
    return slug_of(stem)


def impact_dependants(text: str) -> list:
    """The dependants an `## Impact — proposed` block lists (numbered lines), or [] without the block."""
    _, body = last_section(text, "Impact — proposed")
    if body is None:
        return []
    return [x.casefold() for x in re.findall(r"^\s*\d+\.\s+([A-Za-z0-9][\w-]*)", body, re.M)]


def chunk_lines(n: int, slug: str, text: str, depends: str, why: str) -> str:
    return f"  {n}. {slug} — {text}\n     depends on: {depends}\n     why this line: {why}\n"


# ---------------------------------------------------------------- the blocks
def breakdown_block(rec: Path, text: str) -> tuple[str, str]:
    """PLAN §3.3. Three chunks named after the record's slug (chunk 3 depends on chunk 1); after an impact block, the
    replacement chunk before the removal chunk (E16). A rewrite (a PM answer after the last proposal) notes the words."""
    p = slug_of(rec.stem)
    today = date.today().isoformat()
    heading = f"## Breakdown — proposed {today}"
    pi, _ = last_section(text, "Breakdown — proposed")
    ai, answer = last_section(text, "Breakdown — PM answer")
    rewrite = f"Rewritten from the PM's words: {answer.strip().splitlines()[0] if answer and answer.strip() else ''}\n" if ai is not None and (pi is None or ai > pi) else ""
    deps = impact_dependants(text)
    if deps:
        removed = removed_node(text, rec.stem)
        body = (rewrite + "Chunks:\n"
                + chunk_lines(1, f"{p}-replacement", f"the replacement for what `{deps[-1]}` needed from `{removed}` (`{p}-replacement`)", "none",
                              "the kept dependant must have its replacement before the removal lands")
                + chunk_lines(2, f"{p}-removal", f"retire `{removed}` and the dependants the PM retired with it", "chunk 1",
                              "the removal is safe only once the replacement is delivered")
                + "Order and reasons: 1 first because the kept dependant needs it; 2 last because it removes what 1 replaces\n"
                + "Not split further because: one replacement, one removal\n"
                + "Alternatives considered: remove first and rebuild after; one node for both\n")
        return heading, body
    third_node = f"{p}-streak" if os.environ.get("FAKE_HARNESS_E5") else f"{p}-remind"
    third_dep = "none" if os.environ.get("FAKE_HARNESS_E5") else "chunk 1"
    body = (rewrite + "Chunks:\n"
            + chunk_lines(1, f"{p}-log", f"a member logs one entry for today (`{p}-log`)", "none", "the smallest thing a member can see working")
            + chunk_lines(2, f"{p}-streak", f"a member sees the streak over the last seven days (`{p}-streak`)", "none", "reads the log; nothing else")
            + chunk_lines(3, f"{p}-remind", f"a member gets a reminder at a chosen time (`{third_node}`)", third_dep, "needs the entries from chunk 1")
            + "Order and reasons: 1 first because both others read it; 2 before 3 because the streak de-risks the read model the reminder also uses\n"
            + "Not split further because: each chunk is one capability a member sees on its own\n"
            + "Alternatives considered: one node for the whole request; a finer split with the list as its own chunk; reminders first\n")
    return heading, body


def impact_block(rec: Path, text: str) -> tuple[str, str]:
    """PLAN §3.4: the dependants come from the @node tags under code/ (every tagged node but the removed one)."""
    removed = removed_node(text, rec.stem)
    heading = f"## Impact — proposed {date.today().isoformat()}"
    tags = tags_in_code()
    deps = [] if os.environ.get("FAKE_HARNESS_NO_DEPENDANTS") else [n for n in sorted(tags) if n != removed]
    L = [f"Removing or changing: {removed} — a member loses {removed.replace('-', ' ')}", "Dependants (source in brackets):"]
    for i, d in enumerate(deps, 1):
        L += [f"  {i}. {d} [tags: {tags[d]}; tree: names \"{removed}\"]",
              f"     what stops working: a member using {d.replace('-', ' ')} no longer reaches {removed.replace('-', ' ')}",
              f"     options: retire it too | keep it by a replacement for what it needed | narrow the removal to keep {d} working | postpone",
              f"     recommended: keep it by a replacement — {d} is delivered and in use" if i == len(deps) else f"     recommended: retire it too — nothing else needs {d}"]
    if not deps:
        L.append("  (none found: tags, tree, glossary)")
    L += ["Rules and decisions affected: none",
          f"Stored data: {removed.replace('-', '_')} table — keep | migrate to the replacement | delete; recommended: keep",
          "Possible, unverified: none"]
    return heading, "\n".join(L) + "\n"


def challenge_findings(text: str, who: str) -> str:
    """One finding as always; on a record with an impact block, one more per tagged dependant the block omits (E20)."""
    lines = [f"- [{who}] one finding, fixed: a wording made precise"]
    _, body = last_section(text, "Impact — proposed")
    if body is not None:
        removed = re.search(r"^\s*removing or changing\s*:\s*([\w-]+)", body, re.I | re.M)
        removed = removed.group(1).casefold() if removed else ""
        listed = set(impact_dependants(text))
        for node, file in sorted(tags_in_code().items()):
            if node != removed and node not in listed:
                lines.append(f"- [{who}] the impact block omits the tagged dependant `{node}` (@node {node} in {file}); list it with its options before approve (E20)")
    return "\n".join(lines) + "\n"


def block(step: str, mode_challenger: bool, rec: Path, reviewer: str = None) -> tuple[str, str]:
    """(heading, body) to write for this step."""
    text = rec.read_text(encoding="utf-8")
    if mode_challenger:
        who = reviewer or "fake"
        if step == "define.challenge":
            return f"## Findings — {step}", challenge_findings(text, who)
        return f"## Findings — {step}", f"- [{who}] one finding, fixed: a wording made precise\n"
    if step == "define.breakdown":
        return breakdown_block(rec, text)
    if step == "define.impact":
        return impact_block(rec, text)
    if step == "deliver.plan":
        return "## Plan", ("What changes for the user: the fake plan. What will not change: everything else.\n\n"
                          "## Tasks\n- [ ] T001 [P] [login] write the component, in code/backend/auth/auth.py\n"
                          "- [ ] T002 [login] write its test, in code/backend/auth/test_auth.py\n")
    if step == "deliver.execute":
        return "## Tasks (executed)", "- [x] T001 [P] [login] write the component, in code/backend/auth/auth.py\n- [x] T002 [login] write its test\n"
    return f"## {step}", f"done by the fake harness: {step}\n"


def discuss_block(rec: Path) -> tuple[str, str]:
    """`--discuss`: the notes of define.discuss. On a child, a proposed correction of the breakdown (E4): the parent's
    chunks minus the dropped ones, plus one new chunk depending on this one; on any other record, one line."""
    text = rec.read_text(encoding="utf-8")
    fm = front_matter(text)
    if not fm.get("parent"):
        return "## define.discuss", "discussed with the PM (fake): one capability, its criteria and its place in the tree\n"
    parent = ROOT / fm["parent"]
    ptext = parent.read_text(encoding="utf-8")
    _, body = last_section(ptext, "Breakdown — proposed")
    chunks = re.findall(r"^\s*(\d+)\.\s+([A-Za-z0-9][\w-]*)\s+[—–-]+\s+(.*\S)\s*$", body or "", re.M)
    dropped = set()
    for q in sorted(parent.parent.glob("*.md")):
        if q.name == "QUEUE.md":
            continue
        qfm = front_matter(q.read_text(encoding="utf-8"))
        if qfm.get("parent") == fm["parent"] and qfm.get("step") in ("define.dropped", "deliver.dropped"):
            dropped.add(slug_of(q.stem))
    mine = int(fm.get("chunk") or 1)
    p = slug_of(parent.stem)
    L = [f"Building chunk {mine} showed the split is missing a capability. Proposed correction:", "Chunks:"]
    n = 0
    deps_of = {}
    for _, slug, ctext in chunks:
        if slug in dropped:
            continue
        n += 1
        dep = "none" if n == 1 else "chunk 1"
        deps_of[slug] = n
        L.append(chunk_lines(n, slug, ctext, dep, "kept from the confirmed breakdown").rstrip("\n"))
    n += 1
    L.append(chunk_lines(n, f"{p}-settings", f"a member sets the options chunk {mine} turned out to need (`{p}-settings`)",
                         f"chunk {deps_of.get(slug_of(rec.stem), 1)}", f"found necessary while building chunk {mine}").rstrip("\n"))
    L += ["Order and reasons: the confirmed order stands; the new chunk last because it depends on this one",
          "Not split further because: the new chunk is one capability",
          "Alternatives considered: fold the options into this chunk; one node for the whole request"]
    return "## define.discuss", "\n".join(L) + "\n"


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
    if len(sys.argv) == 3 and sys.argv[1] == "--discuss":
        rec = ROOT / sys.argv[2]
        if not rec.is_file():
            print(f"fake harness: no record at {sys.argv[2]}")
            return 1
        heading, body = discuss_block(rec)
        append(rec, heading, body)
        print(f"fake harness: wrote `{heading}` into {sys.argv[2]} (the PM's step; not advanced)")
        return 0
    prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else sys.stdin.read()
    record, step, exits = parse(prompt)
    if not record or not step:
        print("fake harness: no record or step in the prompt")
        return 1
    if os.environ.get("FAKE_HARNESS_SHOW_RUNMD"):
        run_md = ROOT / "changes" / "runs" / Path(record).stem / "run.md"
        print("fake harness: run.md now reads:\n" + run_md.read_text(encoding="utf-8") if run_md.exists() else "fake harness: no run.md yet")
    if stalled(step):
        print(f"fake harness: stalling at {step} (FAKE_HARNESS_STALL)")
        return 0
    rec = ROOT / record
    challenger = "Mode: challenger" in prompt
    reviewer = re.search(r"reviewer pass `([^`]+)`", prompt)
    heading, body = block(step, challenger, rec, reviewer.group(1) if reviewer else None)
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
