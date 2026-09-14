"""
How often does one failure move a subtask to a different agent?

The allocator scores every (subtask, agent) pair and subtracts a penalty from
agents that already failed the subtask. Whether that penalty changes anything
depends on the gap between the best and second-best agent: a subtask whose
top-two margin is below delta + delta_last is re-routed after a single failure,
one above delta_max never is. Those are statements about the score distribution,
not about the constants, so they have to be measured.

This reads the subtasks the decomposer actually produced in our runs --- logged
per question in results/**/details/*.json --- and reproduces the allocator's
score exactly: the sum of two cosine similarities, question text against agent
description and question type against agent description. Margins are reported
over the distinct subtasks and per scene, since the runs are not balanced across
scenes.

    python -m experiments.measure_routing_margins

Writes results/routing_margins.json and prints the summary quoted in Sec. IV-B.
"""

import json
import re
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sentence_transformers import SentenceTransformer, util

from heart.core.schema import AgentType
from heart.orchestrator.allocator import SemanticTaskAssigner

PROJECT_ROOT = Path(__file__).parent.parent
DETAILS = "results/**/details/*.json"
OUT = PROJECT_ROOT / "results" / "routing_margins.json"

# Penalty constants, from heart/orchestrator/allocator.py.
DELTA, DELTA_LAST, DELTA_MAX = 0.16, 0.12, 0.60

SCENES = ("Beechwood", "Benevolence", "Merom")


def collect() -> List[Tuple[str, str, str]]:
    """(prompt, question_type, scene) for every logged subtask, de-duplicated."""
    seen, out = set(), []
    for path in PROJECT_ROOT.glob(DETAILS):
        try:
            data = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        scene = next((s for s in SCENES if s in path.name), "other")
        for q in (data.get("questions") or {}).values():
            prompt, qtype = q.get("prompt"), q.get("question_type")
            if not (prompt and qtype):
                continue
            key = (prompt.strip(), qtype)
            if key in seen:
                continue
            seen.add(key)
            out.append((prompt.strip(), qtype, scene))
    return out


def margins(rows: List[Tuple[str, str, str]]) -> List[float]:
    """
    Top-two score gap per subtask, using the allocator's own scoring.

    The model name and the agent descriptions are taken from the allocator
    rather than restated here, so this cannot drift from what runs.
    """
    model = SentenceTransformer(
        SemanticTaskAssigner.__init__.__defaults__[0], device="cpu")
    agents = model.encode([a.description for a in AgentType], convert_to_tensor=True)
    prompts = model.encode([r[0] for r in rows], convert_to_tensor=True)
    types = model.encode([r[1] for r in rows], convert_to_tensor=True)
    scores = util.cos_sim(prompts, agents) + util.cos_sim(types, agents)
    out = []
    for i in range(len(rows)):
        top = sorted(scores[i].tolist(), reverse=True)
        out.append(top[0] - top[1])
    return out


def summarise(values: List[float]) -> Dict:
    lo = sum(v < DELTA + DELTA_LAST for v in values) / len(values)
    hi = sum(v > DELTA_MAX for v in values) / len(values)
    return {
        "n": len(values),
        "min": round(min(values), 4), "max": round(max(values), 4),
        "mean": round(st.mean(values), 4), "median": round(st.median(values), 4),
        "below_delta_plus_last": round(lo, 4),
        "above_delta_max": round(hi, 4),
    }


def main() -> int:
    rows = collect()
    if not rows:
        print(f"no logged subtasks under {DETAILS}")
        return 1
    values = margins(rows)

    per_scene = defaultdict(list)
    for (_, _, scene), m in zip(rows, values):
        per_scene[scene].append(m)

    report = {
        "constants": {"delta": DELTA, "delta_last": DELTA_LAST, "delta_max": DELTA_MAX},
        "overall": summarise(values),
        "per_scene": {s: summarise(v) for s, v in sorted(per_scene.items())},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + "\n")

    o = report["overall"]
    print(f"{o['n']} distinct subtasks; margin {o['min']:.2f}-{o['max']:.2f}, "
          f"mean {o['mean']:.2f}, median {o['median']:.2f}")
    print(f"  below delta+delta_last ({DELTA + DELTA_LAST:.2f}): "
          f"{o['below_delta_plus_last']:.0%}  (one failure re-routes)")
    print(f"  above delta_max ({DELTA_MAX:.2f}):            "
          f"{o['above_delta_max']:.0%}  (never re-routed)")
    print(f"\n{'scene':14}{'n':>6}{'mean':>8}{'<d+dl':>8}{'>dmax':>8}")
    for scene, s in report["per_scene"].items():
        print(f"{scene:14}{s['n']:6}{s['mean']:8.2f}"
              f"{s['below_delta_plus_last']:8.0%}{s['above_delta_max']:8.0%}")
    print(f"\n-> {OUT.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
