# Changes from Original DELTA

This directory contains an adapted version of [DELTA](https://github.com/clear-nus/delta) (Licensed under AGPL-3.0) for integration with the HEART framework.

## New Files (HEART additions)
- `delta_planner.py` — Programmatic wrapper matching HEART's planner interface
- `prompt_heart.py` — Extended pruning/problem prompts with HEART constraint injection
- `data/example.py` — Task examples for 40 HEART tasks across 3 scenes (with GT costs)
- `data/scene_graph.py` — Scene graphs and robot configs for 3 HEART evaluation scenes

## Modified Files
- `delta.py` — Added `run_pipeline()` function for programmatic invocation
- `prompt.py` — Minor format adjustments for HEART scene graph structure
- `llm/llm.py` — Added `OpenAIModel` class (standard OpenAI API, replacing Azure-only client)
- `planner.py` — Path adjustments for HEART project structure

## Unchanged Files
- `llm/llm_utils.py`, `utils/utils.py` — No modifications
- `LICENSE`, `NOTICE` — Original DELTA license (AGPL-3.0)
