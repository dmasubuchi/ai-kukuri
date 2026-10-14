#!/bin/sh
# Create a new Kukuri workspace from this kit, or repair an existing one.
#
#   scripts/init-workspace.sh <target-dir>            create (target must not exist or be empty)
#   scripts/init-workspace.sh --repair <target-dir>   add only the files that are missing; never overwrite
#
# Nothing outside <target-dir> is written.
set -eu
kit=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd -P)
mode=create
if [ "${1:-}" = "--repair" ]; then mode=repair; shift; fi
target=${1:-}
if [ -z "$target" ]; then
  echo "usage: init-workspace.sh [--repair] <target-dir>" >&2; exit 2
fi
if [ "$mode" = create ] && [ -e "$target" ] && [ -n "$(ls -A "$target" 2>/dev/null)" ]; then
  echo "stop: target is not empty: $target (use --repair to add missing files)" >&2; exit 2
fi
if [ "$mode" = repair ] && [ ! -d "$target" ]; then
  echo "stop: not a directory: $target" >&2; exit 2
fi
mkdir -p "$target"
target=$(CDPATH= cd -- "$target" && pwd -P)
for d in bin rules skills registry runtime tasks projects input output \
         knowledge/journal knowledge/pages knowledge/records; do
  mkdir -p "$target/$d"
done
# copy a file only when the destination does not exist (never overwrite)
put() { [ -e "$2" ] || [ -L "$2" ] || cp "$1" "$2"; }
for f in "$kit"/bin/*; do put "$f" "$target/bin/$(basename "$f")"; done
put "$kit/rules/common.md" "$target/rules/common.md"
for d in "$kit"/skills/*/; do
  name=$(basename "$d")
  mkdir -p "$target/skills/$name"
  put "$d/SKILL.md" "$target/skills/$name/SKILL.md"
done
put "$kit/templates/AGENTS.md" "$target/AGENTS.md"
put "$kit/templates/CLAUDE.md" "$target/CLAUDE.md"
put "$kit/templates/registry-projects.json" "$target/registry/projects.json"
put "$kit/templates/registry-paths.json" "$target/registry/paths.json"
put "$kit/templates/mcp.json" "$target/runtime/mcp.json"
put "$kit/templates/workspace.gitignore" "$target/.gitignore"
if [ ! -e "$target/runtime/machine.json" ] && [ ! -L "$target/runtime/machine.json" ]; then
python3 - "$target" <<'PY'
import json, sys
root = sys.argv[1]
machine = {
    "machine": "this-machine",
    "workspace_root": root,
    "projects_root": root + "/projects",
    "input_root": root + "/input",
    "output_root": root + "/output",
    "knowledge_root": root + "/knowledge",
    "tasks_root": root + "/tasks",
    "writable_roots": [root],
}
with open(root + "/runtime/machine.json", "w", encoding="utf-8") as f:
    json.dump(machine, f, ensure_ascii=False, indent=2); f.write("\n")
PY
fi
[ -e "$target/tasks/baseline.json" ] || python3 -B "$target/bin/kukuri-tasks" init >/dev/null
chmod +x "$target"/bin/* 2>/dev/null || true
echo "workspace ready ($mode): $target"
