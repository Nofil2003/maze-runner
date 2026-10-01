#!/usr/bin/env bash
#
# verify.sh - run every row of the "Checking your work" table from the project
# brief and compare against the expected numbers.
#
# This is a development tool. It is NOT part of the submission zip.
#
# Usage:
#   ./verify.sh              run every row
#   ./verify.sh q3           run only the rows for question 3
#   ./verify.sh q1 q2 q5     run the rows for several questions
#
# Path cost and steps must match exactly for the optimal algorithms (BFS, IDS,
# UCS, A*). The brief allows the node counts to differ slightly, so a mismatch
# there is reported as a warning unless it is off by more than 25%, which means
# something is actually wrong.

set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT="${PROJECT_DIR:-$HERE/maze_runner}"
PYTHON="${PYTHON:-python3}"
EXPANDED_TOLERANCE=25   # percent

RED=$'\033[31m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'; DIM=$'\033[2m'; OFF=$'\033[0m'
if [ ! -t 1 ]; then RED=; GREEN=; YELLOW=; DIM=; OFF=; fi

# question | runner.py arguments | expected cost | expected steps | expected expanded
ROWS=(
  "q1|-l maze_small -a dfs|50|50|82"
  "q1|-l maze_medium -a dfs|162|162|233"
  "q2|-l maze_tiny -a bfs|8|8|27"
  "q2|-l maze_medium -a bfs|66|66|407"
  "q2|-l open_glade -a bfs|32|32|344"
  "q3|-l maze_small -a dls -d 60|50|50|52"
  "q3|-l maze_small -a dls -d 30|CUTOFF|-|32"
  "q4|-l maze_small -a ids|50|50|1352"
  "q5|-l griever_alley -a ucs|42|28|50"
  "q5|-l ivy_maze -a ucs|70|64|418"
  "q6|-l greedy_trap -a gbfs|52|25|60"
  "q6|-l maze_medium -a gbfs|80|80|81"
  "q7|-l greedy_trap -a astar|25|25|155"
  "q7|-l maze_big -a astar|124|124|679"
  "q8|-l keys_tiny -p keys -a bfs|26|26|490"
  "q8|-l keys_small -p keys -a bfs|54|54|1723"
)

wanted() {   # wanted <question>  -> 0 if this question should run
  [ $# -eq 0 ] && return 0
  local q="$1"; shift
  [ ${#FILTER[@]} -eq 0 ] && return 0
  local f
  for f in "${FILTER[@]}"; do
    [ "$q" = "$(echo "$f" | tr '[:upper:]' '[:lower:]')" ] && return 0
  done
  return 1
}

FILTER=("$@")
pass=0; fail=0; warn=0; skipped=0

printf '%-38s %10s %8s %10s   %s\n' "Command" "Cost" "Steps" "Expanded" "Result"
printf '%s\n' "----------------------------------------------------------------------------------------"

for row in "${ROWS[@]}"; do
  IFS='|' read -r q args wantCost wantSteps wantExp <<< "$row"
  wanted "$q" || continue

  out="$(cd "$PROJECT" && $PYTHON runner.py $args -q --timeout 120 2>&1)"

  gotCost=""; gotSteps=""
  if grep -q 'path cost' <<< "$out"; then
    gotCost="$(sed -n 's/.*path cost \([0-9.]*\),.*/\1/p' <<< "$out" | head -1)"
    gotSteps="$(sed -n 's/.*path cost [0-9.]*, \([0-9]*\) steps.*/\1/p' <<< "$out" | head -1)"
  elif grep -q 'CUTOFF' <<< "$out"; then
    gotCost="CUTOFF"; gotSteps="-"
  fi
  gotExp="$(sed -n 's/^Nodes expanded: *\([0-9]*\).*/\1/p' <<< "$out" | head -1)"
  [ -z "$gotExp" ] && gotExp="-"

  status="${GREEN}PASS${OFF}"; note=""
  if grep -q 'ERROR' <<< "$out"; then
    status="${DIM}TODO${OFF}"
    note="$(sed -n 's/^Result: *ERROR - *//p' <<< "$out" | head -1)"
    skipped=$((skipped+1))
  elif grep -qE 'INVALID PATH|no path found|timed out' <<< "$out"; then
    status="${RED}FAIL${OFF}"
    note="$(sed -n 's/^Result: *//p' <<< "$out" | head -1)"
    fail=$((fail+1))
  elif [ "$gotCost" != "$wantCost" ] || [ "$gotSteps" != "$wantSteps" ]; then
    status="${RED}FAIL${OFF}"
    note="expected cost $wantCost / $wantSteps steps"
    fail=$((fail+1))
  elif [ "$gotExp" != "$wantExp" ]; then
    diff=$(( gotExp > wantExp ? gotExp - wantExp : wantExp - gotExp ))
    if [ $(( diff * 100 / wantExp )) -gt $EXPANDED_TOLERANCE ]; then
      status="${RED}FAIL${OFF}"
      note="expanded $gotExp vs expected $wantExp - too far off, check the conventions"
      fail=$((fail+1))
    else
      status="${YELLOW}WARN${OFF}"
      note="expanded $gotExp vs expected $wantExp - small differences are allowed"
      warn=$((warn+1))
    fi
  else
    pass=$((pass+1))
  fi

  printf '%-38s %10s %8s %10s   %b %s\n' "$args" "${gotCost:--}" "${gotSteps:--}" "$gotExp" "$status" "$note"
done

echo
echo "pass: $pass   warn: $warn   fail: $fail   not implemented yet: $skipped"
echo
echo "${DIM}Q9 is not in this table. Check it with:"
echo "  cd maze_runner && $PYTHON runner.py -l keys_medium -p keys -a astar -H keyhunt -q"
echo "  tiers: <=7000 = 2 marks, <=2600 = 3 marks, <=1200 = 4 marks (UCS baseline: 9695)${OFF}"

[ $fail -gt 0 ] && exit 1
exit 0
