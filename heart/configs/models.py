# HEART Configuration

# All available reasoning agents — workflow creates nodes for whichever agents are selected
REASONING_AGENTS = {
    "capability_reasoner": {"model": "gpt-4o", "temperature": 0.0},
    "environmental_reasoner": {"model": "gpt-4o", "temperature": 0.0},
    "path_reasoner": {"model": "gpt-4o", "temperature": 0.0},
    "feasibility_reasoner": {"model": "gpt-4o", "temperature": 0.0},
    "constraint_reasoner": {"model": "gpt-4o", "temperature": 0.0},
    "homogeneous_reasoner": {"model": "gpt-4o", "temperature": 0.0},
    # 3-agent ablation (combined-scope agents)
    "physical_reasoner": {"model": "gpt-4o", "temperature": 0.0},
    "spatial_reasoner": {"model": "gpt-4o", "temperature": 0.0},
}

# Decomposer config
DECOMPOSER_CONFIG = {
    "model": "o4-mini",
    "temperature": 0.7,
}

# LLM Allocator config (used only when allocator_type="llm")
LLM_ALLOCATOR_CONFIG = {
    "model": "gpt-4o",
    "temperature": 0.0,
}

# Synthesis agent config
SYNTHESIS_CONFIG = {
    "model": "gpt-4o",
    "temperature": 0.0,
}

# Planner config (LLM-CoT)
PLANNER_CONFIG = {
    "model": "gpt-4o",
    "temperature": 0.0,
}

# TypeBased allocator only — fixed task type to agent mapping
# HEART allocator and LLM allocator determine this dynamically
TYPEBASED_MAPPING = {
    "ROBOT_CAPABILITY_ANALYSIS": "capability_reasoner",
    "ACTION_FEASIBILITY": "capability_reasoner",
    "OBJECT_DISCOVERY": "environmental_reasoner",
    "SCENE_UNDERSTANDING": "environmental_reasoner",
    "ROBOT_DISCOVERY": "path_reasoner",
    "PATH_PLANNING": "path_reasoner",
    "ROUTE_OPTIMIZATION": "path_reasoner",
    "PHYSICAL_FEASIBILITY": "feasibility_reasoner",
    "TASK_DEPENDENCY_ANALYSIS": "constraint_reasoner",
    "ACTION_SEQUENCE_CONSTRAINTS": "constraint_reasoner",
    "CONTEXTUAL_CONSTRAINTS": "constraint_reasoner",
}

# Token budget for allocation
TOKEN_BUDGET = 20000

# Agent memory — inject previous Q&A into prompts
USE_AGENT_MEMORY = True
