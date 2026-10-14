#!/bin/sh
# Journal -> Living Wiki -> TODO, end to end, with fictional data only.
# Usage: examples/demo.sh [workspace-dir]   (default: a temporary directory)
set -eu
kit=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd -P)
ws=${1:-$(mktemp -d)/workspace}
"$kit/scripts/init-workspace.sh" "$ws" >/dev/null
cd "$ws"
J="python3 -B bin/kukuri-journal"; W="python3 -B bin/kukuri-wiki"; T="python3 -B bin/kukuri-tasks"
echo "== 1. record what happened (Journal)"
$J add --kind decision --author alice --date 2026-03-02 --time 10:00 \
  --source "Acme kickoff meeting notes (fictional)" \
  --text "Acme Portal will be hosted on Cloud A." \
  --wiki "wiki:acme-portal#hosting = Acme Portal is hosted on Cloud A."
echo "== 2. plan the wiki update (nothing is written)"
$W plan --date 2026-03-02
echo "== 3. apply"
$W apply --date 2026-03-02 --write >/dev/null
echo "== 4. a later AI proposal does not override the decision"
$J add --kind proposal --author bot --date 2026-03-09 --time 09:30 \
  --source "assistant suggestion (fictional)" \
  --text "Cloud B might be cheaper." \
  --wiki "wiki:acme-portal#hosting = Acme Portal should move to Cloud B."
$W apply --date 2026-03-09 --write >/dev/null
echo "== 5. the owner decides later: the old claim moves to history, with source and date"
$J add --kind decision --author alice --date 2026-03-16 --time 11:00 \
  --source "Acme steering meeting notes (fictional)" \
  --text "Move Acme Portal to Cloud B." \
  --wiki "wiki:acme-portal#hosting = Acme Portal is hosted on Cloud B."
$W apply --date 2026-03-16 --write >/dev/null
cat knowledge/pages/acme-portal.md
echo "== 6. a TODO whose completion is backed by a journal entry"
id=$($J add --kind result --author alice --date 2026-03-20 --time 17:00 \
  --source "Acme acceptance report (fictional)" --text "Acme Portal acceptance test passed." \
  | python3 -c "import json,sys;print(json.load(sys.stdin)['id'])")
$J evidence "$id" > evidence.json
python3 - <<'PY'
import json
e = json.load(open("evidence.json"))
json.dump({"title": "Confirm Acme Portal acceptance", "owner": "alice", "evidence": [e]}, open("proposal.json", "w"))
json.dump({"status": "done", "evidence": [e]}, open("done.json", "w"))
PY
task=$($T add --file proposal.json | python3 -c "import json,sys;print(json.load(sys.stdin)['id'])")
$T update "$task" --expected-revision 0 --file done.json >/dev/null
echo "== 7. check"
$W check
echo "demo finished: $ws"
