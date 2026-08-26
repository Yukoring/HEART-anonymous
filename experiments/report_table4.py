"""
Table IV, with the Triple-S row computed and the published rows alongside it.

The four published conditions are quoted from the submitted manuscript so the
new row can be read against them without re-running anything. Triple-S is
computed from `results/planner_*/metrics.csv`.

Merom is restricted to the eight tasks the published Merom cells use. mr_3 and
mr_4 are excluded there because DELTA cannot plan for homogeneous multi-robot
teams, and a row computed over a different task set would not be comparable.

    python -m experiments.report_table4
"""

import argparse
import csv
import glob
import math
import os
import re
import sys
import zipfile
from collections import defaultdict
from typing import Dict, List, Optional
from xml.etree import ElementTree as ET

NS = {"table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
      "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0"}

SCENES = [("BW", "Beechwood_0"), ("BN", "Benevolence_1"), ("MR", "Merom_1")]
MEROM_TASKS = {"mr_0", "mr_1", "mr_2", "mr_5", "mr_6", "mr_7", "mr_8", "mr_9"}

# Quoted from Table IV of the submitted manuscript: (PlanSR, ci, step, plan_tok, total_tok)
PUBLISHED = {
    ("BW", "w/o HEART", "LLM-CoT"): (56.7, 7.9, 1.16, 11.4, 11.4),
    ("BW", "+ HEART",   "LLM-CoT"): (77.3, 6.7, 1.09, 12.5, 125.9),
    ("BW", "w/o HEART", "DELTA"):   (64.0, 7.7, 1.07, 39.3, 39.3),
    ("BW", "+ HEART",   "DELTA"):   (86.0, 5.6, 1.07, 45.6, 161.4),
    ("BN", "w/o HEART", "LLM-CoT"): (16.7, 6.0, 1.01, 10.1, 10.1),
    ("BN", "+ HEART",   "LLM-CoT"): (60.7, 7.8, 1.05, 11.2, 117.6),
    ("BN", "w/o HEART", "DELTA"):   (6.7, 4.0, 1.17, 38.5, 38.5),
    ("BN", "+ HEART",   "DELTA"):   (74.0, 7.0, 1.09, 43.1, 148.9),
    ("MR", "w/o HEART", "LLM-CoT"): (22.5, 9.2, 1.44, 12.2, 12.2),
    ("MR", "+ HEART",   "LLM-CoT"): (65.0, 10.5, 1.33, 13.3, 150.8),
    ("MR", "w/o HEART", "DELTA"):   (18.8, 8.6, 1.32, 42.7, 42.7),
    ("MR", "+ HEART",   "DELTA"):   (76.2, 9.3, 1.07, 46.8, 181.0),
}


def _cells(row) -> List[str]:
    out = []
    for cell in row.findall("table:table-cell", NS):
        repeat = int(cell.get("{%s}number-columns-repeated" % NS["table"], 1))
        text = "".join("".join(p.itertext()) for p in cell.findall("text:p", NS))
        out.extend([text] * min(repeat, 60))
    return out


def ground_truth_steps(ods_path: str) -> Dict[str, int]:
    """Optimal plan length per task, from the workbook's summary sheet."""
    root = ET.fromstring(zipfile.ZipFile(ods_path).read("content.xml"))
    steps, seen_header = {}, False
    for table in root.iter("{%s}table" % NS["table"]):
        if table.get("{%s}name" % NS["table"]) != "Summary":
            continue
        for row in table.findall("table:table-row", NS):
            values = [v for v in _cells(row) if v.strip()]
            if values and values[0] == "Task":
                seen_header = True
            elif seen_header and values and re.match(r"^(bw|bn|mr)_\d+$", values[0]):
                steps[values[0]] = int(values[1])
    return steps


def binomial_ci(successes: int, n: int) -> float:
    """Half-width of the 95% interval, as the manuscript reports it."""
    if n == 0:
        return float("nan")
    p = successes / n
    return 1.96 * math.sqrt(p * (1 - p) / n) * 100


def load_triple_s(results_root: str) -> Dict[str, List[dict]]:
    """Newest completed Triple-S run per scene."""
    by_scene: Dict[str, List[dict]] = {}
    for abbr, scene in SCENES:
        candidates = sorted(glob.glob(f"{results_root}/planner_{scene}_*/metrics.csv"),
                            key=os.path.getmtime, reverse=True)
        for path in candidates:
            rows = [r for r in csv.DictReader(open(path))
                    if r.get("condition") == "baseline_triple_s"]
            if abbr == "MR":
                rows = [r for r in rows if r["task_id"] in MEROM_TASKS]
            if len(rows) >= 50:  # a completed sweep, not a probe
                by_scene[abbr] = rows
                break
    return by_scene


def summarise(rows: List[dict], gt_steps: Dict[str, int]) -> Optional[dict]:
    if not rows:
        return None
    n = len(rows)
    valid = [r for r in rows if r.get("plan_valid") == "True"]

    ratios = [int(r["plan_steps_count"]) / gt_steps[r["task_id"]]
              for r in valid if r["task_id"] in gt_steps and int(r["plan_steps_count"])]
    mean = lambda xs: sum(xs) / len(xs) if xs else float("nan")

    return {
        "n": n,
        "valid": len(valid),
        "plan_sr": len(valid) / n * 100,
        "ci": binomial_ci(len(valid), n),
        "step_ratio": mean(ratios),
        "step_ratio_n": len(ratios),
        "plan_tok": mean([int(r.get("planner_tokens") or 0) for r in rows]) / 1000,
        "total_tok": mean([int(r.get("workflow_total_tokens") or 0) for r in rows]) / 1000,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="results")
    parser.add_argument("--exp", default="../exp")
    args = parser.parse_args()

    triple_s = load_triple_s(args.results)
    if not triple_s:
        print("no completed Triple-S run found")
        return 1

    header = (f"{'Scene':<6} {'Config':<12} {'Planner':<9} "
              f"{'PlanSR (%)':>15} {'Step Ratio':>11} {'Plan Tok(k)':>12} {'Total Tok(k)':>13}")
    print(header)
    print("-" * len(header))

    for abbr, scene in SCENES:
        gt = ground_truth_steps(f"{args.exp}/TaskPlanning_{abbr}.ods")
        for config in ("w/o HEART", "+ HEART"):
            for planner in ("LLM-CoT", "DELTA"):
                sr, ci, step, plan_tok, total_tok = PUBLISHED[(abbr, config, planner)]
                print(f"{abbr:<6} {config:<12} {planner:<9} "
                      f"{sr:9.1f} ± {ci:<3.1f} {step:11.2f} {plan_tok:12.1f} {total_tok:13.1f}")

        row = summarise(triple_s.get(abbr, []), gt)
        if row:
            missing = "" if row["step_ratio_n"] else "   (no GT steps)"
            print(f"{abbr:<6} {'Triple-S':<12} {'—':<9} "
                  f"{row['plan_sr']:9.1f} ± {row['ci']:<3.1f} "
                  f"{row['step_ratio']:11.2f} {row['plan_tok']:12.1f} {row['total_tok']:13.1f}"
                  f"{missing}")
            print(f"{'':<6} {'':<12} {'':<9} {'':>4}({row['valid']}/{row['n']})"
                  f"{'':>6} step ratio over {row['step_ratio_n']} valid plans")
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
