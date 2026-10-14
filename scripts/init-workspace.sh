#!/bin/sh
# Thin POSIX wrapper. The implementation is scripts/init_workspace.py (portable).
#   scripts/init-workspace.sh [--lang en|ja] [--repair] <target-dir>
set -eu
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
for py in python3 python; do
  if command -v "$py" >/dev/null 2>&1; then exec "$py" -B "$here/init_workspace.py" "$@"; fi
done
echo "stop: python3 is required (3.9 or later)" >&2
exit 2
