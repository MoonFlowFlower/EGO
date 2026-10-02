#!/usr/bin/env sh
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
if ! command -v python3 >/dev/null 2>&1; then
  printf '%s\n' 'Python 3.10+ is required. Nothing will be installed automatically.' >&2
  exit 2
fi
exec python3 run.py memory "$@"
