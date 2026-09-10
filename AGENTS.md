# AGENTS.md — editing the workflow studio itself

This repository holds the framework (workflows as YAML) and the tool that
draws them. Any AI editing it follows `README.md` → "The change loop":
edit YAML → `python3 tools/validate.py` → challenger review → `python3
tools/build.py` → save. `SCHEMA.md` is the contract; `framework/README.md`
is the operating reference the workflows describe; `framework/test-cases.md`
is the regression suite — re-run its verdicts after any workflow change.

Never edit `framework/steps.md` or `studio.html` by hand (generated).
Never add a field to a workflow without adding it to `SCHEMA.md` and the
validator first. Never mark a conventions sentence as workflow behaviour.
