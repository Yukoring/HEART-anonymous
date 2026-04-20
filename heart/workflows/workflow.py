"""
HEART Workflow — LangGraph Pipeline

Constructs the LangGraph StateGraph that implements the full HEART pipeline.
Configurable for all experimental conditions:

- Agent count: 5 heterogeneous, 3 merged, or 1 homogeneous
- Allocator type: "heart" (Sentence-BERT), "llm" (GPT-4o), "type_based" (rule)
- Planner type: "llm_cot", "delta", or None (reasoning only)
- skip_decompose: Use pre-decomposed questions (for ablation experiments)

Usage:
    workflow = create_workflow(agents=[...], allocator_type="heart", planner_type="llm_cot")
    result = workflow.invoke(state)
"""

from typing import List, Optional
from langgraph.graph import StateGraph, END

from heart.core.state import SystemState
from heart.workflows.nodes import (
    decompose_node,
    allocate_node,
    executor_node,
    synthesize_node,
    plan_node,
    metrics_collection_node,
)
from heart.workflows.edges import (
    check_decomposition_quality,
    make_agent_router,
    route_from_allocator_to_synthesis,
)


def create_workflow(
    agents: List[str],
    allocator_type: str = "heart",
    planner_type: Optional[str] = None,
    skip_decompose: bool = False,
    checkpointer=None,
) -> StateGraph:
    """
    Create a HEART workflow with configurable agents, allocator, and planner.

    Args:
        agents: List of agent IDs (e.g., ["capability_reasoner", ...])
        allocator_type: "heart", "llm", "type_based", or variants
        planner_type: "llm_cot", "delta", or None (reasoning only)
        skip_decompose: If True, skip decomposition and start from allocate
                        (requires state to have pre-populated questions)
        checkpointer: Optional LangGraph checkpoint saver

    Returns:
        Compiled LangGraph workflow
    """
    workflow = StateGraph(SystemState)

    # ========== Stage 1: Decomposition (optional) ==========
    if not skip_decompose:
        workflow.add_node("decompose", decompose_node)

    # ========== Stage 2: Allocation ==========
    workflow.add_node("allocate", allocate_node)

    # ========== Stage 3: Agent Executors (dynamic) ==========
    for agent_id in agents:
        workflow.add_node(
            f"{agent_id}_executor",
            lambda state, aid=agent_id: executor_node(state, aid)
        )

        router = make_agent_router(agent_id)
        workflow.add_conditional_edges(
            "allocate",
            router,
            {f"{agent_id}_executor": f"{agent_id}_executor", END: END}
        )

        workflow.add_edge(f"{agent_id}_executor", "allocate")

    # ========== Stage 4: Synthesis (Q&A formatting) ==========
    workflow.add_node("synthesize", synthesize_node)

    # ========== Stage 5: Plan (optional) ==========
    if planner_type:
        workflow.add_node("plan", plan_node)

        workflow.add_conditional_edges(
            "allocate",
            route_from_allocator_to_synthesis,
            {"synthesize": "synthesize", END: END}
        )
        workflow.add_edge("synthesize", "plan")
        workflow.add_edge("plan", END)
    else:
        workflow.add_node("metrics_collection", metrics_collection_node)

        workflow.add_conditional_edges(
            "allocate",
            route_from_allocator_to_synthesis,
            {"synthesize": "synthesize", END: END}
        )
        workflow.add_edge("synthesize", "metrics_collection")
        workflow.add_edge("metrics_collection", END)

    # ========== Edges & Entry Point ==========
    if skip_decompose:
        # Start directly from allocate (questions already in state)
        workflow.set_entry_point("allocate")
    else:
        workflow.add_conditional_edges(
            "decompose",
            check_decomposition_quality,
            {"allocate": "allocate", "decompose": "decompose"}
        )
        workflow.set_entry_point("decompose")

    return workflow.compile(checkpointer=checkpointer)
