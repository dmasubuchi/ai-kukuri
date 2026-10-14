#!/bin/sh
# One-command installer for KUKURI Kit.
#
#   ./install.sh [--repair] <workspace-dir>        from a checkout
#   curl -fsSL <url>/install.sh | KUKURI_KIT_TARBALL=<archive url> sh -s -- <workspace-dir>
#
# Environment:
#   KUKURI_KIT_TARBALL  URL of a .tar.gz of this repository (needed only when not run from a checkout)
#   KUKURI_KIT_SHA256   optional SHA-256 of that archive; the install stops if it does not match
#
# Nothing outside <workspace-dir> (and a temporary directory for the download) is written.
set -eu

fail() { echo "kukuri-kit: $*" >&2; exit 2; }

command -v python3 >/dev/null 2>&1 || fail "python3 is required (3.9 or later)"
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' \
  || fail "Python 3.9 or later is required"

here=$(CDPATH= cd -- "$(dirname -- "$0")" 2>/dev/null && pwd -P || echo "")
kit=""
if [ -n "$here" ] && [ -f "$here/scripts/init-workspace.sh" ]; then
  kit="$here"
else
  [ -n "${KUKURI_KIT_TARBALL:-}" ] || fail "not run from a checkout: set KUKURI_KIT_TARBALL to the archive URL"
  command -v curl >/dev/null 2>&1 || fail "curl is required to download the archive"
  tmp=$(mktemp -d) || fail "cannot create a temporary directory"
  trap 'rm -rf "$tmp"' EXIT INT TERM
  curl -fsSL "$KUKURI_KIT_TARBALL" -o "$tmp/kit.tar.gz" || fail "download failed"
  if [ -n "${KUKURI_KIT_SHA256:-}" ]; then
    actual=$(python3 -c 'import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' "$tmp/kit.tar.gz")
    [ "$actual" = "$KUKURI_KIT_SHA256" ] || fail "archive checksum mismatch"
  fi
  mkdir "$tmp/src"
  tar -xzf "$tmp/kit.tar.gz" -C "$tmp/src" --strip-components=1 || fail "cannot extract the archive"
  [ -f "$tmp/src/scripts/init-workspace.sh" ] || fail "the archive is not a KUKURI Kit checkout"
  kit="$tmp/src"
fi

sh "$kit/scripts/init-workspace.sh" "$@"
echo "next:  cd <workspace> && bin/kukuri-journal add --help   (see README)"
