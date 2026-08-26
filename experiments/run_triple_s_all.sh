#!/usr/bin/env bash
# Triple-S across all three scenes, at the scale Table IV uses.
#
# Beechwood and Benevolence run all 15 tasks. Merom runs 8 — mr_3 and mr_4 are
# left out because DELTA cannot handle homogeneous multi-robot teams, so the
# published Merom cells are all N=80 and Triple-S has to sit on the same task
# set to be comparable.
#
# Waits for any run already in flight before starting, so it can be launched
# while Beechwood is still going.
set -u

cd "$(dirname "$0")/.."
PY=./.venv/bin/python

wait_for_running() {
    while pgrep -f "run_planner.py" > /dev/null; do sleep 30; done
}

echo "=== $(date +%H:%M) waiting for any run already in flight ==="
wait_for_running

for spec in "Benevolence_1|" "Merom_1|--tasks 0 1 2 5 6 7 8 9"; do
    scene="${spec%%|*}"
    extra="${spec#*|}"
    echo "=== $(date +%H:%M) $scene $extra ==="
    $PY experiments/run_planner.py --scenes "$scene" $extra \
        --iterations 10 --conditions baseline_triple_s \
        > "results/triple_s_${scene}.log" 2>&1
    echo "=== $(date +%H:%M) $scene done (exit $?) ==="
done

echo "=== $(date +%H:%M) all scenes complete ==="
