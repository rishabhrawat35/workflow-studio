# Workflow Studio

Business workflows as code. One YAML file per workflow, a map of how they connect, and a renderer that draws any one of them or all of them together.

Claude edits the files; Rira reviews the picture.

## Layout

```
SCHEMA.md            what a workflow file may contain (the contract)
DECISIONS.md         why things are the way they are (append-only)
map.yaml             workflow of workflows: registry + grouping
workflows/*.yaml     one file per workflow
studio.html          the renderer — open in a browser
tools/validate.py    checks every rule in SCHEMA.md
tools/build.py       embeds the YAML into studio.html (runs validate first)
tools/studio.template.html   renderer source
build/               generated artifact copy, not hand-edited
```

## The change loop

1. Edit `workflows/*.yaml` and, if a workflow was added or moved, `map.yaml`.
2. `python3 tools/validate.py` — must print `OK`.
3. Challenger review: an independent reviewer checks the diff against `SCHEMA.md`, `map.yaml` and what was actually discussed. Findings are fixed before anything is saved.
4. `python3 tools/build.py` → refreshes `studio.html`.
5. Commit. Republish the artifact.

Nothing is committed that fails step 2 or 3.

Requires Python 3 with PyYAML (`pip install pyyaml`). The renderer itself has no dependencies.

## Cross-workflow links

A `handoff` step with `to: <workflow-id>.<step-id>` is the only way two workflows connect. The map view draws these links; nothing is written twice.
