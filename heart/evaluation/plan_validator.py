"""
Plan Validator

Validates generated plans against manually authored ground truth PDDL specifications
using the VAL plan validator (https://github.com/KCL-Planning/VAL).

Each task has a corresponding pair of PDDL files in data/pddl/:
  - domain/{scene}_{domain}_domain.pddl: action definitions with preconditions and effects
  - problem/{scene}_{domain}_problem.pddl: initial state and goal conditions

Validation process:
  1. DELTA plans are already in PDDL action format → passed directly to VAL.
  2. LLM-CoT plans are in natural language format (e.g., "navigate(robot, roomA, roomB)")
     → converted to PDDL format using an LLM with the domain PDDL as context → then validated.
  3. VAL checks that every action's preconditions are satisfied at execution time
     and that the goal state is achieved after the final action.

Validation is a measurement tool, NOT part of the planning pipeline.
Conversion tokens/time are NOT counted in experiment metrics.
"""

import os
import subprocess
import tempfile
import time
from typing import Dict, Any, List, Optional
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent  # HEART/


def get_pddl_paths(task_id: str, scene_name: str,
                   pddl_paths: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """
    Ground truth PDDL domain and problem file paths.

    `pddl_paths` overrides the household task registry, which is how the farm
    scenes — generated rather than registered — are validated with the same code.
    """
    if pddl_paths:
        return pddl_paths
    from heart.configs.tasks import get_pddl_domain_path, get_pddl_problem_path
    return {
        "domain": str(PROJECT_ROOT / get_pddl_domain_path(task_id)),
        "problem": str(PROJECT_ROOT / get_pddl_problem_path(scene_name, task_id)),
    }


def run_val(domain_file: str, problem_file: str, plan_file: str) -> Dict[str, Any]:
    """
    Run VAL validator on a plan file.

    Returns:
        {"valid": bool, "info": str}
    """
    if not os.path.isfile(domain_file):
        return {"valid": False, "info": f"Domain file not found: {domain_file}"}
    if not os.path.isfile(problem_file):
        return {"valid": False, "info": f"Problem file not found: {problem_file}"}
    if not os.path.isfile(plan_file):
        return {"valid": False, "info": f"Plan file not found: {plan_file}"}

    command = f"Validate -v {domain_file} {problem_file} {plan_file}"
    try:
        p = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
        )
        output, err = p.communicate(timeout=30)
        output_str = output.decode("utf-8", errors="replace")

        if "Plan valid" in output_str:
            return {"valid": True, "info": "Plan valid"}
        else:
            # Extract repair advice if available
            repair_phrase = "Plan Repair Advice:"
            if repair_phrase in output_str:
                msg = output_str[output_str.index(repair_phrase) + len(repair_phrase):]
                if "Failed plans:" in msg:
                    msg = msg[:msg.index("Failed plans:")]
                return {"valid": False, "info": msg.strip()}
            return {"valid": False, "info": "Plan did not achieve the goal"}

    except subprocess.TimeoutExpired:
        p.kill()
        return {"valid": False, "info": "VAL timeout"}
    except FileNotFoundError:
        return {"valid": False, "info": "VAL validator not installed"}


def convert_llm_cot_to_pddl(
    plan_steps: List[str],
    task_id: str,
    scene_name: str,
    model_name: str = "gpt-4o",
    pddl_paths: Optional[Dict[str, str]] = None,
) -> List[str]:
    """
    Convert LLM-CoT natural language plan to PDDL action format using LLM.

    Uses only the domain PDDL (action definitions) as context — NOT the problem PDDL
    (which contains the goal/answer).

    Args:
        plan_steps: LLM-CoT plan actions (e.g., ["navigate(robot, room1, room2)", ...])
        task_id: Task identifier for loading domain PDDL
        scene_name: Scene name for context

    Returns:
        List of PDDL action strings (e.g., ["(goto robot room1 room2)", ...])
    """
    from langchain_openai import ChatOpenAI

    # Load domain PDDL (actions only, NO problem/goal)
    domain_path = get_pddl_paths(task_id, scene_name, pddl_paths)["domain"]

    if not os.path.isfile(domain_path):
        print(f"[Validator] Domain PDDL not found: {domain_path}")
        return []

    with open(domain_path, "r") as f:
        domain_pddl = f.read()

    # Build conversion prompt
    plan_text = "\n".join(plan_steps)

    prompt = f"""Convert the following robot action plan into PDDL plan format.

## PDDL Domain (available actions):
```
{domain_pddl}
```

## Plan to convert:
```
{plan_text}
```

## Conversion rules:
1. Convert each action one-to-one. The output must have EXACTLY the same number of actions as the input. Do not add, remove, merge, split, or reorder any actions.
2. Match each action name to the closest action defined in the domain PDDL above.
   READ THE COMMENTS in the domain carefully — they explain when to use each action variant
   (e.g., place_in vs put_in, open vs open_dishwasher, check vs check_drone).
3. If an action has NO matching action in the domain, keep the original name as-is.
4. Keep ALL identifiers (robot names, object names, room names) EXACTLY as they appear. Do not rename or substitute any identifier.
5. Each action must have the same number of parameters as defined in the domain PDDL. If the original plan is missing a parameter (e.g., room), infer it from the navigation context in the plan.
6. Output format: (action_name arg1 arg2 ...) — one per line.
7. Never convert "place" to "drop". "place" maps to place_on, place_in, or put_in based on the domain.

## Example:
Input plan:
navigate(my_robot, roomA, roomB)
pick(my_robot, obj1)
place(my_robot, obj1, surface1)

Domain actions: goto(?a ?r1 ?r2), pick(?a ?i ?r), place_on(?a ?i1 ?i2 ?r)

Output:
(goto my_robot roomA roomB)
(pick my_robot obj1 roomB)
(place_on my_robot obj1 surface1 roomB)

## Output ONLY the converted PDDL plan below, no explanations:"""

    try:
        llm = ChatOpenAI(model=model_name, temperature=0.0)
        response = llm.invoke(prompt)
        content = response.content.strip()

        # Parse response — extract lines that look like PDDL actions
        pddl_actions = []
        for line in content.split("\n"):
            line = line.strip()
            # Remove markdown code block markers
            if line.startswith("```"):
                continue
            # Accept lines that start with (
            if line.startswith("(") and line.endswith(")"):
                pddl_actions.append(line)

        return pddl_actions

    except Exception as e:
        print(f"[Validator] LLM conversion failed: {e}")
        return []


def validate_plan(
    plan_steps: List[str],
    task_id: str,
    scene_name: str,
    planner_type: str = "llm_cot",
    pddl_paths: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Validate a plan against ground truth PDDL.

    For DELTA: plan_steps are already in PDDL format → validate directly.
    For LLM-CoT: convert to PDDL using LLM → validate.

    Args:
        plan_steps: Plan action strings
        task_id: Task identifier (e.g., "serve_food")
        scene_name: Scene name (e.g., "Benevolence_1")
        planner_type: "llm_cot" or "delta"

    Returns:
        {
            "valid": bool,
            "info": str,
            "pddl_plan": List[str],  # PDDL actions used for validation
            "conversion_time": float,  # LLM conversion time (0 for DELTA)
        }
    """
    if not plan_steps:
        return {
            "valid": False,
            "info": "Empty plan",
            "pddl_plan": [],
            "conversion_time": 0.0,
        }

    paths = get_pddl_paths(task_id, scene_name, pddl_paths)

    # Convert plan to PDDL format if needed
    conversion_time = 0.0
    if planner_type == "delta":
        # DELTA plans are already in PDDL format
        pddl_actions = plan_steps
    else:
        # LLM-CoT: convert using LLM
        convert_start = time.time()
        pddl_actions = convert_llm_cot_to_pddl(plan_steps, task_id, scene_name,
                                               pddl_paths=paths)
        conversion_time = time.time() - convert_start
        print(f"[Validator] Converted {len(plan_steps)} actions → {len(pddl_actions)} PDDL actions ({conversion_time:.1f}s)")

    if not pddl_actions:
        return {
            "valid": False,
            "info": "No PDDL actions after conversion",
            "pddl_plan": [],
            "conversion_time": conversion_time,
        }

    # Write plan to temp file and validate
    with tempfile.NamedTemporaryFile(mode="w", suffix=".plan", delete=False) as f:
        f.write("\n".join(pddl_actions) + "\n")
        plan_file = f.name

    try:
        result = run_val(paths["domain"], paths["problem"], plan_file)
        result["pddl_plan"] = pddl_actions
        result["conversion_time"] = conversion_time
        return result
    finally:
        os.unlink(plan_file)
