# HEART: Heterogeneous Expert Agents for Robotic Task Planning

A multi-LLM framework that coordinates role-specialized reasoning agents under a token budget to improve robotic task planning.

## Overview

HEART decomposes task instructions into atomic reasoning questions, routes them to specialized expert agents via a Sentence-BERT-based allocator, and synthesizes the results into constraints for downstream planners.

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
│   │   ├── base.py             # Abstract base with memory and token estimation
│   │   ├── reasoning_agent.py  # Unified agent for all 5 expert roles
│   │   ├── decomposer_agent.py # Stage 1: instruction decomposition
│   │   ├── synthesis_agent.py  # Stage 4: Q&A cross-validation
│   │   └── allocator_agent.py  # LLM allocator baseline
│   ├── configs/
│   │   ├── tasks.py            # 40 task definitions across 3 scenes
│   │   └── models.py           # LLM model configs and agent mappings
│   ├── core/
│   │   ├── schema.py           # Pydantic models (AgentType, TaskType, etc.)
│   │   └── state.py            # LangGraph state and merge functions
│   ├── evaluation/
│   │   └── plan_validator.py   # PDDL + VAL plan validation
│   ├── orchestrator/
│   │   ├── allocator.py        # HEART allocator (SBERT + capacity + penalty)
│   │   ├── allocator_type.py   # TypeBased allocator baseline
│   │   ├── allocator_llm.py    # LLM allocator baseline
│   │   ├── executor.py         # Agent execution coordinator
│   │   ├── synthesizer.py      # Q&A text formatter
│   │   └── task_decomposer.py  # Decomposition orchestrator
│   ├── prompts/                # All prompt templates
│   │   ├── system_prompts.py   # Per-agent system prompts
│   │   ├── reasoning.py        # Per-agent human prompts
│   │   ├── decomposition.py    # Decomposer prompts
│   │   ├── synthesis.py        # Synthesis prompts
│   │   ├── descriptions.py     # Shared type/agent descriptions
│   │   └── allocation.py       # LLM allocator prompt
│   ├── utils/
│   │   ├── data_filter.py      # Role-aligned environment data filtering
│   │   └── urdf_parser.py      # Robot URDF spec extraction
│   └── workflows/
│       ├── workflow.py          # LangGraph pipeline construction
│       ├── nodes.py             # Node functions (decompose, allocate, execute, etc.)
│       └── edges.py             # Conditional routing logic
│
├── planners/                    # Planning backends
│   ├── llm_cot/                 # LLM Chain-of-Thought planner
│   │   ├── llm_cot_planner.py   # GPT-4o with CoT reasoning
│   │   └── llm_as_planner_prompts.py  # Action definitions and examples
│   └── delta/                   # DELTA LLM-to-PDDL planner (adapted)
│       ├── delta_planner.py     # HEART integration wrapper
│       ├── delta.py             # Original pipeline (domain→prune→problem→solve)
│       ├── prompt.py            # Original DELTA prompts
│       ├── prompt_heart.py      # HEART-extended prompts
│       ├── planner.py           # Fast Downward solver interface
│       ├── data/                # Scene graphs and task examples
│       └── llm/                 # LLM client interfaces
│
├── experiments/                 # Experiment scripts
│   ├── _common.py               # Shared utilities (run trials, metrics, validation)
│   ├── configs.py               # Experiment condition definitions
│   ├── run_planner.py           # Planner comparison (baseline vs HEART)
│   ├── run_agent_role.py        # Agent role ablation (5 vs 3 vs 1 agents)
│   ├── run_allocator_ablation.py # Allocator component ablation
│   ├── run_budget_plan.py       # Token budget scaling
│   └── run_type_ablation.py     # Task type granularity ablation
│
├── data/
│   ├── pddl/                    # Ground truth PDDL for plan validation
│   │   ├── domain/              # 40 domain files (action definitions)
│   │   └── problem/             # 40 problem files (initial state + goals)
│   ├── robots/                  # Robot URDF files (Fetch, JR2 Kinova, Quadrotor)
│   └── scenes/                  # Scene graph JSON files (3 Gibson scenes)
```

## Setup

```bash
# Install dependencies (using uv)
uv sync

# Or with pip
pip install -e .

# Configure API key
cp .env.example .env
# Edit .env and add your OpenAI API key

# Verify installation
python heart/tests/test_basic.py
```

## Running Experiments

All experiment scripts support `--scenes`, `--tasks`, `--iterations`, and `--conditions` arguments.

```bash
# Planner comparison: baseline vs HEART (Table IV in paper)
python experiments/run_planner.py --scenes Beechwood_0 --iterations 10

# Agent role ablation: 5 vs 3 vs 1 agents (Table II)
python experiments/run_agent_role.py --iterations 10

# Allocator component ablation (Table III)
python experiments/run_allocator_ablation.py --budgets 10000 20000 40000

# Token budget scaling
python experiments/run_budget_plan.py --budgets 10000 20000 40000

# Quick single-task test
python heart/tests/test_planning.py --scene Beechwood_0 --task 0
```

Results are saved to `results/` with CSV metrics, detail JSONs, and plan files.

## Evaluation

**Scenes** (from Gibson dataset):
| Scene | Rooms | Objects | Focus | Tasks |
|-------|-------|---------|-------|-------|
| Beechwood_0 | 9 | 74 | Logical sequencing | 15 |
| Benevolence_1 | 5 | 55 | Physical feasibility | 15 |
| Merom_1 | 7 | 65 | Multi-robot coordination | 10 |

**Plan validation**: Plans are validated against manually authored PDDL specifications using the [VAL plan validator](https://github.com/KCL-Planning/VAL). Ground truth PDDL files are in `data/pddl/`.

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- OpenAI API key (GPT-4o, o4-mini)
- [VAL plan validator](https://github.com/KCL-Planning/VAL) (install separately)
- Fast Downward planner (for DELTA backend, optional)

## License

The HEART framework code is provided for academic review purposes.
The DELTA planner (`planners/delta/`) is licensed under AGPL-3.0 — see `planners/delta/LICENSE`.
