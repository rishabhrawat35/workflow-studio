# Orchestration layer 1

The layer that makes the framework closed: nothing moves except along an
edge in the workflow YAML, nobody runs a step except the role mapped to
it, and every state is a file.

## Four things it manages

1. **State** — in the change record's front matter: `step`, `lane`
   (small | full), `waiting_on` (PM | AI), `since`, `failed_passes`,
   `rerun_count`, `role`, `mode`, `command`, `history` (every edge taken,
   with its condition and time). The workflow YAML is the state machine.
2. **Multi-agent** — six roles in `roles.yaml`, one per step: Sorter,
   Writer, Planner, Builder, Verifier, Challenger. Each role is a fresh
   context that reads only the step's listed `inputs`. A Builder never
   edits the business side; a Writer never writes code; a Challenger never
   rewrites.
3. **Challenger mode** — steps with `mode: challenger` return findings
   only. Zero findings on non-trivial work → `orchestrate.py rerun`, which
   selects the next framing from the step's list; the small lane never
   reruns; when every framing is used, the work proceeds with what it has.
4. **Agent mode** — steps with `mode: agent` produce the step's `output`
   into the record; a decision with judgment in it is `agent` with the
   role that just did the work (Verifier decides `passes`, Builder decides
   `tasks-done`, Sorter decides routing). `mode: pm` steps wait for the PM
   and are left only with `--answer`. `mode: auto` is routing without
   judgment: handoffs and ends only.

## The tool

`framework/tools/orchestrate.py`:

- `check` — the system is CLOSED or it is not. Every step mapped to
  exactly one role and mode; PM-input steps are `pm` and only they;
  challenger steps have framings; handoffs and ends are `auto` and only
  they; every command enters a real non-routing step; entry
  commands enter `define.intake`; every exit resolves; every exit of a
  decision has a condition and no two share one. Run first; every command
  template runs it.
- `next <record>` — the current step, mode, role, inputs, framing, the
  findings block status, what the PM gives, what the step produces, the
  numbered legal exits, and the last edges taken. The AI does exactly that
  and nothing else.
- `advance <record> --to <exit> --when <condition> [--answer …]` — the
  only way to move. Refuses: an exit not in the YAML; a decision without
  its condition or with a mismatched one; leaving a PM step without
  `--answer`; leaving a challenger step without a `## Findings — <step>`
  block, or with zero findings while a rerun framing is unused (full
  lane); a fourth `execute` or an `accept` after three failed passes (the
  edge `passes → execute` is itself the count); `--lane` anywhere but at
  start or leaving `define.sort`; any exit from a handoff other than its
  `to:` (the drawing's local end is recorded as `closes`). Resets the pass
  count on any return to plan; records every edge, answer and lane change
  in `history`.
- `start <record> --command speckit.<name>` — only for entry commands
  (all at `define.intake`); any other command continues a record already
  at its step or is refused, so `/speckit-implement` on a fresh file can
  never create state at `execute`. `rerun` — next framing.

## Commands

`commands.yaml`: Spec Kit names where the meaning overlaps
(`speckit.constitution`, `specify`, `clarify`, `checklist`, `plan`,
`tasks`, `analyze`, `implement`, `converge`, `bug.assess`, `bug.fix`,
`bug.test`, `assess.intake`, `taskstoissues`, `git.commit`) and ours with
the same prefix (`speckit.approve`, `accept`, `rule`, `status`, `why`,
`drop`).
`framework/commands/*.md` are the templates (`$ARGUMENTS` = the PM's
words); `framework/tools/install_commands.py --agent all` installs them in
Spec Kit ≥ 1.0's skills layout (`.claude/skills/speckit-<name>/SKILL.md`,
`.agents/skills/…` for Codex, `.github/skills/…` for Copilot,
`.cursor/skills/…`, `.gemini/commands/speckit.<name>.toml`), invoked as
`/speckit-<name>`. Where a name's meaning differs from Spec Kit's
(`checklist`, `tasks`, `assess.intake`) the command's `does` says so.

Two commands wrap a tool rather than a step, and each checks the record's
step itself (the record's front matter, read with `orchestrate.py`'s own
parser), so neither can act before its gate:

- `speckit.taskstoissues` → `framework/tools/tasks_to_issues.py <record>
  [--repo owner/name] [--dry-run]`. One GitHub issue per task line
  (`- [ ] T001 [P] [node-id] …`) via `gh issue create`: title = id + text,
  body = nodes, record path, lane; label `workflow-studio`; the number is
  written back onto the line as ` → #123`, and a line that already has one
  is skipped, so a rerun after a re-plan exports only the new tasks. Allowed
  at `deliver.execute` or any later Deliver step (the plan is approved);
  refused at `plan`, `challenge-plan`, `approve-plan` and everything
  earlier. It moves nothing: the record stays the source of truth, the
  issues are a mirror, nothing is imported back. `--dry-run` prints what
  would be created and is the default when `gh` is missing. `enters:
  deliver.execute` in `commands.yaml` names the first step it is legal at.
- `speckit.git.commit` → `framework/tools/commit.py <record> [--dry-run]
  [--still-needs-logic]`, the one code commit of `deliver.commit`. Refuses
  outside a git repository, any record not at `deliver.commit` (so nothing
  is committed before the PM's "accepted"), and an index that already holds
  changes outside the delivery. Then: regenerates the three indexes (the
  decision log must validate), sets each delivered node's `Status:
  delivered <version>` (the node file's last commit) and the record's
  outcome, moves the record `commit → was-rule → done` (or `→
  resume-define` with `--still-needs-logic`) through `orchestrate.py
  advance`, stages exactly the component folders the task lines name, the
  node files, this record's decisions (and existing ones that gained
  `superseded_by`), the indexes, the record, and `changes/QUEUE.md` /
  `architecture.md` when modified, and commits as `<record slug>: <title>`
  with nodes and decision ids in the body. The lesson decision and, for a
  rule, the architecture edit are written by the AI before the tool runs.
  Only the task lines name code (a path in the trace or plan prose is not
  staged); changed code files no task names are reported and left
  uncommitted. If git refuses the commit (a hook) after the record was
  moved, the record and the node files are restored to `deliver.commit`
  and the index is unstaged, so the tool can simply be run again.

## Guarantees (proven by `check` + the workflow validator)

- No open node: every step reachable from `define.intake`, every step
  reaches an end, every step has an owner role and a mode.
- No invented transition: an AI cannot move a record except along a YAML
  edge with its named condition.
- No silent review skip: the tool refuses to leave a challenger step
  without that step's findings block, and refuses zero findings while a
  framing is unused; it refuses to leave a PM step without the answer.
- No unbounded loop: the `passes → execute` edge is counted by the tool
  and capped at three; the Define↔Deliver ping-pong is PM-driven and
  visible in `history`.
- Resume: `next` on any record tells any AI, in any tool, exactly where it
  is and what to do.
