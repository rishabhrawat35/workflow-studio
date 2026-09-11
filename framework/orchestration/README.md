# Orchestration layer 1

The layer that makes the framework closed: nothing moves except along an
edge in the workflow YAML, nobody runs a step except the role mapped to
it, and every state is a file.

## Four things it manages

1. **State** — in the change record's front matter: `step`, `lane`
   (small | full), `waiting_on` (PM | AI; on a child, `chunk <n>` or
   `parent`), `since`, `failed_passes`, `rerun_count`, `role`, `mode`,
   `command`, `history` (every edge taken, with its condition and time),
   and on a child of a broken-down request `parent`, `chunk` and
   `depends_on`. The workflow YAML is the state machine, with one
   pseudo-state outside it: `waiting` (`step: waiting`, `mode: waiting`),
   the state of a child whose dependency is not yet delivered. `check`
   never sees it; `next` and `advance` handle it; its one exit is the
   release `advance --to define.discuss`, refused until every dependency
   is at `deliver.done` or dropped (a dropped dependency moves
   `waiting_on` to the next unmet one).
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

- `check [<child>]` — the system is CLOSED or it is not. Every step mapped to
  exactly one role and mode; PM-input steps are `pm` and only they;
  challenger steps have framings; handoffs and ends are `auto` and only
  they; every command enters a real non-routing step; entry
  commands enter `define.intake`; every exit resolves; every exit of a
  decision has a condition and no two share one. Run first; every command
  template runs it. With a child record as its argument it also confirms
  the parent file and the parent's `## Breakdown — PM answer` block exist,
  and refuses naming the missing one otherwise (as `next` and `advance`
  on that child do).
- `next <record>` — the current step, mode, role, inputs, framing, the
  findings block status, what the PM gives, what the step produces, the
  numbered legal exits, and the last edges taken. The AI does exactly that
  and nothing else.
- `advance <record> --to <exit> --when <condition> [--answer …]` — the
  only way to move. Refuses: `--answer` at a step that is not a PM step
  (first, before anything about the exit: "<step> is an AI step, not a PM
  step; the runner (or the AI) moves it"); an exit not in the YAML; a decision without
  its condition or with a mismatched one; leaving a PM step without
  `--answer`; leaving a challenger step without a `## Findings — <step>`
  block, or with zero findings while a rerun framing is unused (full
  lane); a fourth `execute` or an `accept` after three failed passes (the
  edge `passes → execute` is itself the count); `--lane` anywhere but at
  start or leaving `define.sort`; any exit from a handoff other than its
  `to:` (the drawing's local end is recorded as `closes`). Resets the pass
  count on any return to plan; records every edge, answer and lane change
  in `history`. For a large request or a removal it also refuses: leaving
  `define.breakdown` without a `## Breakdown — proposed` block that lists
  at least one chunk, or `define.impact` without an `## Impact — proposed`
  block with at least one dependant; `--to spawn` on an answer that is not
  a yes, and `--to breakdown` on one that is; a fourth round of
  `breakdown → confirm-breakdown` or `impact → confirm-impact` (only
  `write` or `drop` after three); `--to breakdown` or `--to impact` with
  no `architecture.md`; `--to impact` while a record in Deliver names a
  node this record names (in `nodes:`, in a task line's `[<id>]` tag, or —
  for this record — in backticks in its body or its PM answers); leaving
  `impact` with a stored-data line that recommends delete; leaving
  `confirm-impact` with an answer that names no choice for a listed
  dependant or for a listed store of data; leaving `breakdown` with a
  chunk slug that cannot name a file, a chunk depending on a later chunk,
  or a `## Breakdown — PM answer` block the gate never wrote (the same
  count holds for `## Impact — PM answer` at `impact`); `write` or `drop`
  from a reopened `confirm-breakdown` while the parent has children;
  `spawn` twice on one confirmation, with two chunks on one node and no
  dependency between them, with a chunk slug that is the slug of an
  existing record, or with a revision that removes a chunk in Deliver or
  makes it wait; `--to revise-breakdown` on a record without `parent` or
  on a delivered chunk; the release of a waiting child whose dependency is
  not delivered (a dropped dependency hands its own dependencies on);
  `next`, `advance` or `check` on a child whose `step:` was edited past
  `waiting` while a dependency is open. Leaving `spawn` writes
  the child records, the group block in `changes/QUEUE.md` and the
  breakdown decision; every later move of a child or its parent rewrites
  the group block.
- `start <record> --command speckit.<name>` — only for entry commands
  (all at `define.intake`); any other command continues a record already
  at its step or is refused, so `/speckit-implement` on a fresh file can
  never create state at `execute`; a record carrying `parent` is refused
  too (children are created by `define.spawn`). `rerun` — next framing.
- `next <record> --json` — the same as `next`, as one JSON object for the
  runner: `step`, `title`, `type`, `mode`, `role`, `role_card`,
  `waiting_on`, `lane`, `exits` (`to`, `when`, `index`), `command` and
  `template` (the command that enters this step and its template file, if
  any), `what` / `output` / `notes` / `input`, `inputs`, `failed_passes`,
  `rerun_count`, `edges` (how many edges the record has taken) and
  `last_edges` (the last five, each with `from`, `to`, `when`, `at`, and
  `answer` where the PM answered), and for a challenger `framing` and
  `findings`. On a child: `parent`, `chunk`, `depends_on`; on a child or
  a parent: `group` (`title`, the parent's step, `chunks` as `[n, step,
  waiting on]`, `delivered`, `dropped`, `total`, `in_flight`); on a
  waiting child `mode: waiting`, `wait` (the sentence `next` prints),
  `blocked_by` and the single release exit. The text output is unchanged.

## Commands

`commands.yaml`: Spec Kit names where the meaning overlaps
(`speckit.constitution`, `specify`, `clarify`, `checklist`, `plan`,
`tasks`, `analyze`, `implement`, `converge`, `bug.assess`, `bug.fix`,
`bug.test`, `assess.intake`, `taskstoissues`, `git.commit`) and ours with
the same prefix (`speckit.approve`, `accept`, `rule`, `status`, `why`,
`drop`, `run`). `speckit.run` is `meta: true` with `enters: current`: it
wraps the runner (below) and enters whatever step the record is at, so the
rule "every command enters a real non-routing step" cannot name its step;
`check` accepts exactly that pair for a meta command and nothing else, and
`start` refuses it.
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

## Layer 2: the runner

Layer 1 makes the system closed; a person still started every step.
`framework/tools/run.py <record>` (the `/speckit-run` command) starts the AI
steps itself and stops only at a PM step; `run.py --group <parent>` does the
same for a broken-down request, chunk by chunk:

- It loops over `orchestrate.py next --json`. An `auto` step (handoff, end)
  it advances itself along the single exit. An `agent` or `challenger` step
  it runs in a **fresh harness process** with cwd at the product root: role
  isolation, no step sees the conversation that produced the last one. A
  `pm` step it prints in plain words (title, what the PM must provide, the
  options, the exact `advance … --to <exit> [--when <n>] --answer "…"`
  command, the slash command) and stops. After the options it names the
  most common answer — `Most common answer: --to 3 --when 3 ("PM says
  yes")`, the first exit whose condition contains yes / execute / accepted /
  write it — and prints the paste-ready `advance … --answer "yes" &&
  python3 framework/tools/run.py <record>` line (`--harness` appended when
  it is not `claude`); a step whose conditions name none of these (intake)
  gets no such line.
- While a harness session runs, stderr carries a live line `<step> · <role>
  · <harness> · m:ss`, refreshed every 10 s (in place on a TTY, one line per
  refresh otherwise) and a final line with the outcome (`moved`, `changed
  the record`, `did not move; retrying once`, `did not move`, `stuck`);
  stdout carries only the PM stop text and the summary, as before.
- After each spawned step it re-reads `next` and checks the record's history,
  not only its step: exactly one new edge, taken from the step it spawned,
  carrying no PM answer; further edges are accepted only from `auto` steps
  (a harness that also advanced the handoff it landed on). If nothing moved
  it retries once with the harness's last 40 output lines appended, quoted
  as output ("Your previous attempt did not move the record …"); if it still
  did not move, the run stops with the reason and the log path. If the
  record moved in a way the contract forbids, the run stops at once (exit
  4) and says what happened, with the record left as it is for the PM to
  read: a `step:` line edited by hand (no edge in the history), a harness
  that answered a PM step itself, or one that ran on into the next AI step.
  A reviewer session that is not the last must change the record without
  moving it.
- The prompt (`build_prompt`) is: the role card from `roles.yaml` (role,
  mode, what it may and may not do, the inputs it reads, the framing for a
  challenger); the step's title, what, output and notes; the body of the
  command template that enters the step (`$ARGUMENTS` = the record path);
  the record path and "read AGENTS.md first"; the toolbox row (below) when
  it applies; and the contract: write the output into the record under the
  step's heading (a challenger: its findings block), then exactly one
  `advance` call, listed with the legal exits and their conditions; do not
  call `start`, do not edit other records, do not commit; a challenger that
  found nothing is told about `rerun`. Only the template's role and intent
  lines are kept: every numbered line naming `check`, `start`, `next`,
  `advance` or `Repeat` is dropped (the first live run showed the Writer
  following that procedure instead of the contract), and one sentence says
  the runner already ran `check`, started the record and read `next`; the
  "the PM's note" sentence is rewritten, since under the runner there is
  none. When the edge that entered `define.write` or `deliver.plan` carries
  a PM answer starting with "no change" / "the draft stands" / "unchanged",
  the contract adds: change nothing in the draft, write one line under the
  step heading that it is re-submitted unchanged, then advance. The runner
  never puts record content into a prompt, only the path.
- A group. A record whose `next --json` says `mode: waiting` is a PM-visible
  stop: exit 3 with "Waiting: chunk n of <parent> waits for chunk k (<file>
  at <step>) to reach deliver.done; nothing runs until then.", the release
  command and the `--group` command; nothing is spawned. `--group <parent>`
  runs the parent while it is open (a reopened parent stops at
  `confirm-breakdown`; a parent at `spawn` is spawned), then the first
  child in flight, else the first waiting child the release accepts, to its
  end or PM stop; after a close (`deliver.done`, `define.dropped`,
  `deliver.dropped`) it picks again; exit 0 with "group closed: … n of m
  delivered" when every chunk is done or dropped, or "group: nothing to
  run" when the rest is blocked. Without `--group` a child's run stops when
  the child closes. `--group` is refused (exit 4) on a child ("pass its
  parent") and on a record with no children that is not on its way to
  `spawn`. Every close and every PM stop inside a group print the group
  line ("Group: <title> (<parent>) — n of m delivered; k dropped; in
  flight: chunk …"). The two new gates are stops like any PM step: the
  runner prints the question and the paste-ready answer (`--answer "yes"`
  at `confirm-breakdown`; at `confirm-impact` a placeholder the PM fills
  with one line per dependant and per store of data) and never answers
  them itself.
- Harnesses come from `harness.yaml`: `claude` runs `claude -p <prompt>
  --output-format text --allowedTools <list>` (Read, Edit, Write, Glob, Grep,
  `Bash(python3 framework/tools/*)`, `Bash(git status*)`, `Bash(git diff*)`,
  `Bash(git log*)`, `Bash(python3 -m pytest*)`, `Bash(npm test*)`, plus the
  file's `allowed_tools`); `codex` runs `codex exec <prompt> --sandbox
  workspace-write`; `fake` runs `framework/tools/fake_harness.py`, the
  stand-in the test suite uses (`FAKE_HARNESS_STALL` and
  `FAKE_HARNESS_OVERSTEP` make it misbehave on purpose;
  `FAKE_HARNESS_SHOW_RUNMD` makes it echo `run.md` as it stands mid-run). The built-in Bash patterns are narrow on
  purpose: `Bash(python3 *)` is not among them, because `python3 -c` is any
  shell command; a product whose tests or run command need more names them
  in `allowed_tools` (`Bash(npm run test*)`, `Bash(python3 -m app*)`). The
  allow-list is what `claude -p` may run without asking (in `-p` mode a tool
  not on it is denied, not prompted), not a sandbox: Edit and Write reach
  every file, which is why the runner checks the history, not the harness.
  A flag that skips every permission (`--dangerously-skip-permissions`,
  `--dangerously-bypass-approvals-and-sandbox`, `--yolo`, codex's
  `danger-full-access` sandbox) and a tool entry that allows every shell
  command (`Bash`, `Bash(*)`) are refused wherever they appear in the file.
  `run.py --check-harness [--harness …]` verifies the harness is on PATH and
  prints its version; a run refuses before its first step when the harness
  is not on PATH or the record does not exist (no log folder is created).
- Toolbox: `toolbox.yaml` names, per step, the plugin skills an installed
  harness plugin offers (`install_commands.py --with-ecc` installs ECC with
  profile minimal, target claude, hooks off, and exits 1 if a hook is
  registered in `~/.claude/settings.json`). The row reaches the prompt only
  when `architecture.md` contains the file's `enabled_when` string; `never`
  is listed alongside; `check` validates every step key and prints the row
  count. A row with `passes: separate …` (`deliver.verify`) runs one fresh
  session per reviewer, each appending its findings to the record; only the
  last one advances. Hooks are never installed: a hook acts outside the
  record and the orchestrator, so nothing it does is gated.

Exit codes: `0` the record reached an end (one summary line: steps run, PM
stops, seconds per step; with `--group`, the group closed or nothing can be
released); `3` a PM step (the question is printed and
logged) or a waiting child (the wait is printed); `4` a step did not move after the retry, moved in a way the
contract forbids, `--max-steps` (default 60; auto steps count, PM stops do
not) was hit after that many steps, the harness could not be run, or
`--group` named a record that is not a parent; `130`
Ctrl-C (the harness process is stopped with the runner, the summary is
written, the record is whatever the last `advance` wrote). `--dry-run`
prints the prompt and the harness command for the current step and spawns
nothing.

Logs: `<log-dir>/<record-stem>/<n>-<step>.log` (default `changes/runs/`;
the prompt, then each attempt's stdout and stderr; `n` continues across
runs of the same record; a run at a PM step also writes the question as
`<n>-<step>.log`) and `run.md` in the same folder, one section per run that
ran or stopped at something (with `--group`, one folder per record run), with a row per step: n, step, role, harness,
seconds, result (`moved`, `moved (4 sessions)`, `advanced → …`, `waiting on
PM`, `stuck`, `interrupted`; a harness that moved the record but exited
non-zero shows `(harness exit n)`). The section is rewritten at every step
start and end — the header with `outcome: running` and an in-flight row
(`… | running since 13:16:53 |`) before the harness starts, each finished
row as soon as its step ends, the final outcome line last — so a second
terminal always sees the current state.
