"""
Offline re-scoring of saved plans against the numeric PDDL pair.

Every plan produced by the experiments is on disk, and the LLM-CoT plans were
saved in their converted PDDL form as well, so the whole benchmark can be
re-scored without re-running a single LLM call. Each plan is validated twice —
once against the original domain and problem, once against the numeric variant —
so any change in verdict is attributable to the numeric constraints alone rather
than to a difference in how the plan was produced.

Plans still in natural language (`*_llm_cot.plan`, no `_pddl` suffix) are
skipped; their converted counterpart is what VAL reads.

    python -m experiments.rescore_numeric --exp-root ../exp --scene bn

Writes a per-plan CSV and prints where the two protocols disagree.
"""

import argparse
import csv
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Optional, Tuple

from heart.configs.tasks import (
    ABBR_TO_SCENE,
    SCENE_TASKS,
    get_pddl_domain_path,
    get_pddl_problem_path,
)

PROJECT_ROOT = Path(__file__).parent.parent
VAL_TIMEOUT = 30


def run_val(domain: Path, problem: Path, plan: Path) -> Tuple[bool, str]:
    """(valid, reason). The reason is VAL's repair advice, trimmed to one line."""
    try:
        proc = subprocess.run(
            ["Validate", "-v", str(domain), str(problem), str(plan)],
            capture_output=True, timeout=VAL_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except FileNotFoundError:
        sys.exit("VAL not installed — expected `Validate` on PATH")

    out = proc.stdout.decode("utf-8", errors="replace")
    if "Plan valid" in out:
        return True, ""

    match = re.search(r"has an unsatisfied precondition at time \d+\n\((.*?)\)\n", out, re.S)
    if match:
        return False, " ".join(match.group(1).split())
    match = re.search(r"unsatisfied precondition in:\n(\(.*?\))", out)
    if match:
        return False, match.group(1)
    return False, "goal not reached"


def parse_plan_name(path: Path) -> Optional[Dict[str, str]]:
    """
    `bn_1_benevolence_iter2_ablation_semantic_only_10k_llm_cot_pddl.plan`
    -> task bn_1, scene benevolence, iteration 2, the rest as the condition.
    """
    stem = path.stem
    match = re.match(r"^([a-z]{2}_\d+)_([a-z]+)_iter(\d+)_(.*)$", stem)
    if not match:
        return None
    task_id, scene, iteration, rest = match.groups()

    if rest.endswith("_delta_orig"):
        planner, condition = "delta_orig", rest[:-len("_delta_orig")]
    elif rest.endswith("_delta"):
        planner, condition = "delta", rest[:-len("_delta")]
    elif rest.endswith("_llm_cot_pddl"):
        planner, condition = "llm_cot", rest[:-len("_llm_cot_pddl")]
    else:
        return None  # natural-language plan, or a naming we do not recognise

    return {"task_id": task_id, "scene": scene, "iteration": iteration,
            "planner": planner, "condition": condition}


def pddl_pair(task_id: str, scene_name: str, numeric: bool) -> Optional[Tuple[Path, Path]]:
    domain = PROJECT_ROOT / get_pddl_domain_path(task_id)
    problem = PROJECT_ROOT / get_pddl_problem_path(scene_name, task_id)
    if numeric:
        domain = domain.parent.parent / "domain_num" / domain.name
        problem = problem.parent.parent / "problem_num" / problem.name
    if not domain.is_file() or not problem.is_file():
        return None
    return domain, problem


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exp-root", default="../exp", help="directory holding the saved plans")
    parser.add_argument("--scene", default="bn", help="scene abbreviation")
    parser.add_argument("--out", default="results/rescore_numeric.csv")
    parser.add_argument("--limit", type=int, help="stop after this many plans (for a smoke test)")
    args = parser.parse_args()

    scene_name = ABBR_TO_SCENE[args.scene]
    task_ids = {t.id for t in SCENE_TASKS[scene_name]}

    exp_root = Path(args.exp_root)
    plans = sorted(p for p in exp_root.rglob(f"{args.scene}_*.plan"))

    out_path = PROJECT_ROOT / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    skipped = Counter()
    flips = defaultdict(list)

    for plan in plans:
        meta = parse_plan_name(plan)
        if meta is None:
            skipped["unparsed_or_natural_language"] += 1
            continue
        if meta["task_id"] not in task_ids:
            skipped["other_scene"] += 1
            continue

        original = pddl_pair(meta["task_id"], scene_name, numeric=False)
        numeric = pddl_pair(meta["task_id"], scene_name, numeric=True)
        if original is None:
            skipped["no_ground_truth"] += 1
            continue
        if numeric is None:
            skipped["no_numeric_pair"] += 1
            continue

        valid_orig, _ = run_val(*original, plan)
        valid_num, reason = run_val(*numeric, plan)

        rows.append({
            "file": str(plan.relative_to(exp_root)),
            "source": plan.relative_to(exp_root).parts[0],
            **meta,
            "valid_orig": valid_orig,
            "valid_num": valid_num,
            "flip": "" if valid_orig == valid_num else
                    ("orig_only" if valid_orig else "num_only"),
            "reason_num": reason,
        })
        if valid_orig != valid_num:
            flips[meta["task_id"]].append(rows[-1])

        if args.limit and len(rows) >= args.limit:
            break

    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["file"])
        writer.writeheader()
        writer.writerows(rows)

    total = len(rows)
    agree = sum(1 for r in rows if not r["flip"])
    print(f"Re-scored {total} plans ({args.scene}) — {out_path.relative_to(PROJECT_ROOT)}")
    for reason, n in skipped.most_common():
        print(f"  skipped {n}: {reason}")

    print(f"\nOriginal protocol valid: {sum(r['valid_orig'] for r in rows)}/{total}")
    print(f"Numeric  protocol valid: {sum(r['valid_num'] for r in rows)}/{total}")
    print(f"Same verdict: {agree}/{total}")

    if flips:
        print("\nVerdict changes")
        for task_id in sorted(flips):
            changed = flips[task_id]
            kinds = Counter(r["flip"] for r in changed)
            print(f"  {task_id:7} {len(changed):4} plans  {dict(kinds)}")
            for reason, n in Counter(r["reason_num"] for r in changed).most_common(3):
                print(f"          {n:4}  {reason}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
