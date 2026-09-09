# Decisions

Append-only log. Newest at the bottom. Each entry: date, decision, why.

## 2026-09-09 — Approach

- **Workflows as code.** One YAML file per workflow, edited by Claude, reviewed by Rira. Reason: text is diffable, versionable and reliably editable; drawings are not.
- **Repo location:** `~/Downloads/workflow-studio` on Rira's machine. Everything is saved here before any step is considered done.
- **Renderer:** a single self-contained `studio.html` with no external libraries (own layered layout; works offline), also published as a Claude artifact. Two views: one workflow, and the map of all workflows.
- **Cross-workflow links live only in `handoff.to`.** `map.yaml` holds the registry and grouping; links are derived, never typed twice.
- **Layout is automatic.** No coordinates in the files.
- **Schema is minimal.** Fields are added only when a real workflow needs them, logged here first.
- **Change loop:** edit YAML → `python3 tools/validate.py` → independent challenger review of the diff → `python3 tools/build.py` → commit → republish artifact. Nothing is saved without passing validation and review.
- **No invented content.** Workflows are written only from what Rira describes or documents he provides. Business and product case are discussed first; workflows are defined after.
- **Content order:** no workflow exists yet. First step is a discussion of the business case and product case; the first workflow follows from that.

## 2026-09-09 — Scaffold review

- Challenger review of the scaffold found 3 must-fix bugs (JSON embedding corrupted multi-line text; empty `map.yaml` skipped map checks; duplicate error lines) and a dozen minor ones. All fixed before the first commit.
