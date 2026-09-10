#!/usr/bin/env python3
"""Embed map.yaml and workflows/*.yaml (as JSON) into the renderer.

Writes:
  studio.html            full page, open it locally in a browser
  build/studio.artifact.html   same page without the <html>/<head>/<body>
                         wrapper, for publishing as a Claude artifact

Refuses to build if tools/validate.py fails. Also regenerates framework/steps.md via tools/docs.py.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "tools" / "studio.template.html"
OUT = ROOT / "studio.html"
OUT_ART = ROOT / "build" / "studio.artifact.html"


def main() -> int:
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "validate.py")])
    if r.returncode != 0:
        print("build aborted: validation failed")
        return 1

    wf_files = sorted((ROOT / "workflows").glob("*.yaml")) if (ROOT / "workflows").exists() else []
    data = {
        "map": yaml.safe_load((ROOT / "map.yaml").read_text(encoding="utf-8")) or {"groups": []},
        "workflows": [yaml.safe_load(p.read_text(encoding="utf-8")) for p in wf_files],
    }
    # No "<" survives inside the JSON block, so no content can close or re-open the script tag
    payload = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")

    tpl = TEMPLATE.read_text(encoding="utf-8")
    marker = re.compile(r'<script type="application/json" id="data">.*?</script>', re.S)
    # replacement is a function so backslashes in the JSON are never treated as regex escapes
    body, n = marker.subn(lambda _m: f'<script type="application/json" id="data">{payload}</script>', tpl)
    if n != 1:
        print("build aborted: data marker not found exactly once in template")
        return 1

    OUT_ART.parent.mkdir(exist_ok=True)
    OUT_ART.write_text(body, encoding="utf-8")
    # standalone page: everything before <header> (title, fonts, styles) belongs in <head>
    cut = body.index("<header>")
    OUT.write_text(
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        + body[:cut] + "</head>\n<body>\n" + body[cut:] + "\n</body>\n</html>\n",
        encoding="utf-8",
    )
    print(f"built {OUT.name} and {OUT_ART.relative_to(ROOT)} with {len(wf_files)} workflow(s)")
    return subprocess.run([sys.executable, str(ROOT / "tools" / "docs.py")]).returncode


if __name__ == "__main__":
    sys.exit(main())
