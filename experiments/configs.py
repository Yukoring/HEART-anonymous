"""
Experiment configurations for HEART.
Each config defines agents, allocator, planner, and optional settings.
"""

AGENTS_5 = [
    "capability_reasoner", "environmental_reasoner", "path_reasoner",
    "feasibility_reasoner", "constraint_reasoner",
]

AGENTS_1 = ["homogeneous_reasoner"]

AGENTS_3 = ["physical_reasoner", "spatial_reasoner", "constraint_reasoner"]

EXPERIMENTS = {
    # ==================== Agent Role ====================
    "5_agents": {
        "agents": AGENTS_5,
        "allocator_type": "heart",
        "planner_type": "llm_cot",
        "description": "5 heterogeneous agents + LLM-CoT",
    },
    "3_agents": {
        "agents": AGENTS_3,
        "allocator_type": "heart",
        "planner_type": "llm_cot",
        "description": "3 merged agents + LLM-CoT",
    },
    "homogeneous": {
        "agents": AGENTS_1,
        "allocator_type": "heart",
        "planner_type": "llm_cot",
        "description": "1 homogeneous agent + LLM-CoT",
    },

    # ==================== Allocator Comparison ====================
    # Default budget 20k. Override with --budget flag.
    "allocator_heart": {
        "agents": AGENTS_5,
        "allocator_type": "heart",
        "planner_type": "llm_cot",
        "description": "HEART allocator (full)",
    },
    "allocator_llm": {
        "agents": AGENTS_5,
        "allocator_type": "llm",
        "planner_type": "llm_cot",
        "description": "LLM allocator",
    },
    "allocator_type_based": {
        "agents": AGENTS_5,
        "allocator_type": "type_based",
        "planner_type": "llm_cot",
        "description": "TypeBased allocator",
    },

    # ==================== HEART + Planner ====================
    "heart_llm_cot": {
        "agents": AGENTS_5,
        "allocator_type": "heart",
        "planner_type": "llm_cot",
        "description": "HEART + LLM-CoT planner",
    },
    "heart_delta": {
        "agents": AGENTS_5,
        "allocator_type": "heart",
        "planner_type": "delta",
        "description": "HEART + DELTA planner",
    },

    # ==================== Baselines (planner alone) ====================
    "baseline_llm_cot": {
        "agents": None,  # No HEART — planner called directly
        "allocator_type": None,
        "planner_type": "llm_cot",
        "description": "LLM-CoT alone (baseline)",
    },
    "baseline_delta": {
        "agents": None,
        "allocator_type": None,
        "planner_type": "delta",
        "description": "DELTA alone (baseline)",
    },

    # ==================== Allocator Component Ablation ====================
    # 4 conditions: isolate capacity planning and history penalty contributions
    # All use Sentence-BERT routing — only allocation strategy differs
    "ablation_semantic_only": {
        "agents": AGENTS_5,
        "allocator_type": "heart_semantic_only",
        "planner_type": "llm_cot",
        "description": "Ablation: semantic routing only (no capacity, no penalty)",
    },
    "ablation_no_penalty": {
        "agents": AGENTS_5,
        "allocator_type": "heart_no_penalty",
        "planner_type": "llm_cot",
        "description": "Ablation: capacity planning only (no penalty)",
    },
    "ablation_no_capacity": {
        "agents": AGENTS_5,
        "allocator_type": "heart_no_capacity",
        "planner_type": "llm_cot",
        "description": "Ablation: history penalty only (no capacity planning)",
    },
    # "allocator_heart" above serves as the full HEART condition (capacity + penalty)

}

# Token budget options for allocator comparison experiments
BUDGET_OPTIONS = [10000, 20000, 40000, 9999999]
