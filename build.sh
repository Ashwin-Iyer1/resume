#!/bin/sh
# LuaLaTeX build with fail-closed PDF/source checks. Pass --portable and/or --publish.
set -eu
cd "$(dirname "$0")"
exec python3 scripts/build.py "$@"
