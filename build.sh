#!/bin/sh
# Build Simon the Sorcerer from your own copy of the game:
#     ./build.sh "Simon The Sorcerer (1994)(Gamesware)(Disk 01 of 10).adf" ... (discs 1 to 9)
# then: cd recomp && ./simon
# The steps are recipe.json's "build", run by SuperSpider's tools/weave.py.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
SUPERSPIDER="${SUPERSPIDER:-$HOME/stuff/superspider}"
[ $# -gt 0 ] || { echo "usage: $0 DISC01.adf ... DISC09.adf" >&2; exit 2; }
(cd "$SUPERSPIDER" && dune build)
WEAVE_RECIPES="$HERE" exec python3 -I "$SUPERSPIDER/tools/weave.py" build "$@"
