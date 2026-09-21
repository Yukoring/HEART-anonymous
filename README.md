# HEART: Coordinated Heterogeneous Expert Agents for Physically Grounded Robotic Task Planning

A multi-LLM framework that coordinates role-specialized reasoning agents under a
token budget to improve robotic task planning.

## Overview

HEART decomposes task instructions into atomic reasoning questions, routes them
to specialized expert agents via a Sentence-BERT-based allocator, and synthesizes
the results into constraints for downstream planners.

**Pipeline (5 stages):**
1. **Decompose** — LLM breaks instruction into typed reasoning questions
2. **Allocate** — Sentence-BERT assigns questions to expert agents under token budget
3. **Execute** — Each agent reasons with role-filtered environment data
4. **Synthesize** — LLM cross-validates Q&A into clean constraints
5. **Plan** — Downstream planner generates executable actions with constraints

## Project Structure

```
HEART/
├── heart/                      # Core framework
│   ├── agents/                 # LLM agent implementations
│   │   ├── base.py             # Abstract base with memory and token accounting
│   │   ├── reasoning_agent.py  # Unified agent for all 5 expert roles
│   │   ├── decomposer_agent.py # Stage 1: instruction decomposition
│   │   ├── synthesis_agent.py  # Stage 4: Q&A cross-validation
│   │   └── allocator_agent.py  # LLM allocator baseline
│   ├── configs/
│   │   ├── tasks.py            # 40 task definitions across 3 household scenes
│   │   └── models.py           # LLM model configs and agent mappings
│   ├── core/
│   │   ├── schema.py           # Pydantic models (AgentType, TaskType, etc.)
│   │   └── state.py            # LangGraph state and merge functions
│   ├── evaluation/
│   │   ├── plan_validator.py   # PDDL + VAL plan validation
│   │   └── feasibility_oracle.py  # Reach, gripper, and payload limits from URDF
│   ├── orchestrator/
│   │   ├── allocator.py        # HEART allocator (SBERT + capacity + penalty)
│   │   ├── allocator_type.py   # TypeBased allocator baseline
│   │   ├── allocator_llm.py    # LLM allocator baseline
│   │   ├── executor.py         # Agent execution coordinator
│   │   ├── synthesizer.py      # Q&A text formatter
│   │   └── task_decomposer.py  # Decomposition orchestrator
│   ├── prompts/                # All prompt templates
│   └── utils/
│       ├── data_filter.py      # Role-aligned environment data filtering
│       └── urdf_parser.py      # Robot spec extraction (FK-sampled workspace)
│
├── planners/                    # Planning backends
│   ├── llm_cot/                 # LLM Chain-of-Thought planner
│   ├── delta/                   # DELTA LLM-to-PDDL planner (adapted)
│   └── triple_s/                # Triple-S baseline, reimplemented from the paper
│       ├── triple_s_planner.py  # Simplification / Solution / Summary loop
│       ├── demonstrations.py    # Top-k retrieval library with replacement rule
│       └── prompts.py           # Per-stage prompts
│
├── experiments/
│   ├── run_planner.py                # Planner comparison, incl. Triple-S (Table IV)
│   ├── run_agent_role.py             # Agent role ablation, 5 vs 3 vs 1 (Table II)
│   ├── run_allocator_ablation.py     # Allocator component ablation (Table III)
│   ├── run_type_ablation.py          # Task type granularity ablation
│   ├── run_triple_s_all.sh           # Triple-S across all three scenes
│   ├── run_harvesting_planners.py    # Plan generation for the Harvesting domain
│   ├── generate_harvesting_scenes.py # Harvesting scene graphs and problem files
│   ├── build_harvesting_workbook.py  # Recording sheet for the physical runs
│   ├── generate_numeric_pddl.py      # Numeric ground truth from URDF + scene graph
│   ├── rescore_numeric.py            # Re-score saved plans against the numeric pair
│   ├── calibrate_oracle.py           # Check the oracle against hand-labelled cases
│   ├── measure_routing_margins.py    # Top-two score margins the penalty acts on
│   ├── report_table4.py              # Table IV with confidence intervals
│   └── report_infeasibility.py       # Physically infeasible picks per condition
│
└── data/
    ├── pddl/
    │   ├── domain/       # Ground-truth domains, 41 files
    │   ├── problem/      # Ground-truth problems, 41 files
    │   ├── domain_num/   # Numeric domains: size, weight, reach, gripper, payload
    │   └── problem_num/  # Numeric problems with measured object properties
    ├── robots/           # URDFs: Fetch, JR2-Kinova, quadrotor, Summit XL + UR5e
    ├── scenes/           # 3 household scene graphs (Gibson)
    └── harvesting/       # The physical domain
        ├── scenes/       # 5 scene graphs
        ├── placement/    # Measurement sheets for setting up each scene
        └── runs/         # Execution logs from the 45 real-robot runs
```

## Setup

```bash
uv sync                  # or: pip install -e .
cp .env.example .env     # then add your OpenAI API key
python heart/tests/test_basic.py
```

## Running Experiments

All experiment scripts support `--scenes`, `--tasks`, `--iterations`, and
`--conditions`.

```bash
# Planner comparison: LLM-CoT, DELTA, Triple-S, and each with HEART (Table IV)
python experiments/run_planner.py --scenes Beechwood_0 --iterations 10

# Triple-S at the scale Table IV uses, across all three scenes
./experiments/run_triple_s_all.sh

# Agent role ablation: 5 vs 3 vs 1 agents (Table II)
python experiments/run_agent_role.py --iterations 10

# Allocator component ablation (Table III)
python experiments/run_allocator_ablation.py --budgets 10000 20000 40000

# Plans for the Harvesting domain, scored against the numeric ground truth
python -m experiments.run_harvesting_planners --iterations 3
```

Results are written to `results/`, which is not tracked. Analysis scripts read
from there:

```bash
python -m experiments.report_table4              # Table IV with CIs
python -m experiments.measure_routing_margins    # margins behind Sec. IV-B
python -m experiments.rescore_numeric            # numeric vs original verdicts
```

## Evaluation

**Household scenes** (Gibson), 40 instructions in total:

| Scene | Rooms | Objects | Focus | Tasks |
|-------|-------|---------|-------|-------|
| Beechwood_0 | 9 | 74 | Logical sequencing | 15 |
| Benevolence_1 | 5 | 62 | Physical feasibility | 15 |
| Merom_1 | 7 | 65 | Multi-robot coordination | 10 |

**Harvesting**, run on a Summit XL base with a UR5e arm: five scenes holding
four to eight ripe or unripe tomatoes across two stems, one to three of them
beyond the arm's reach or wider than its gripper. Every plan from LLM-CoT,
Triple-S, and HEART + LLM-CoT was executed on the robot over three trials per
scene, for 45 runs. The logs are in `data/harvesting/runs/`; recordings are on
the project page.

**Plan validation.** Plans are checked with the
[VAL plan validator](https://github.com/KCL-Planning/VAL) against ground-truth
PDDL authored from the robot URDF and scene-graph measurements. In the numeric
files (`domain_num/`, `problem_num/`) object dimensions and robot limits are
numeric fluents, so VAL rejects a pick that exceeds reach, gripper width, or
payload rather than the object being absent from the problem.

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- OpenAI API key (GPT-4o, o4-mini)
- [VAL plan validator](https://github.com/KCL-Planning/VAL), installed separately
- Fast Downward (for the DELTA backend, optional)

## License

The HEART framework code is provided for academic review purposes.
The DELTA planner (`planners/delta/`) is licensed under AGPL-3.0 — see
`planners/delta/LICENSE`.
