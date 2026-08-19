#!/bin/bash
# Package src/ into dist/proj.alfredworkflow (a zip with info.plist at its root).
set -euo pipefail
cd "$(dirname "$0")"

plutil -lint src/info.plist
python3 -c "import json,subprocess; json.loads(subprocess.run(['python3','src/scripts/list_projects.py'],capture_output=True,text=True,check=True).stdout)" \
  && echo "list_projects.py emits valid JSON"

mkdir -p dist
rm -f dist/proj.alfredworkflow
(cd src && zip -r -q ../dist/proj.alfredworkflow . -x '.*')
echo "Built dist/proj.alfredworkflow"
