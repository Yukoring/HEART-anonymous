"""
HEART Workflow Edges

LangGraph conditional routing logic that controls the pipeline flow:
- after_decompose: Check question count validity, trigger refinement if needed
- after_allocate: Route to agent execution nodes based on allocations
- after_execute: Continue to next agent, re-allocate, or proceed to synthesis
- after_synthesize: Route to planner or end (if no planner configured)

The allocate → execute → allocate loop continues until all questions are
resolved (completed or failed) or the retry limit is reached.
"""

from typing import Literal
from langgraph.graph import END
from heart.core.state import SystemState


# ==================== Decomposition Edge ====================

def check_decomposition_quality(state: SystemState) -> Literal["allocate", "decompose"]:
    """
    Check decomposition quality — only validates question count (5-20).
    Returns "decompose" for refinement or "allocate" to proceed.
    """
    retry_count = state.get("decompose_num", 0)
    if retry_count >= 2:
        return "allocate"

    questions = state.get("questions", [])
    if len(questions) < 5 or len(questions) > 20:
        return "decompose"

    return "allocate"


# ==================== Dynamic Agent Routing ====================

def make_agent_router(agent_id: str):
    """
    Create a routing function for a specific agent.
    Returns a function that checks if the agent has tasks to process.

    Usage:
        for agent_id in agents:
            router = make_agent_router(agent_id)
            graph.add_conditional_edges("allocator", router, {
                f"{agent_id}_executor": f"{agent_id}_node",
                END: END
            })
    """
    def router(state: SystemState) -> str:
        agent_tasks = state.get("agent_tasks", {}).get(agent_id, set())
        if agent_tasks:
            return f"{agent_id}_executor"
        return END

    # Set function name for debugging
    router.__name__ = f"route_to_{agent_id}"
    return router


# ==================== Allocator to Synthesis Routing ====================

def route_from_allocator_to_synthesis(state: SystemState) -> Literal["synthesize", "__end__"]:
    """
    Check if all tasks are resolved (completed + failed = total).
    If so, proceed to synthesis.
    """
    questions = state.get("questions", {})
    completed = state.get("completed_tasks", {})
    failed = state.get("failed_tasks", {})

    total_questions = len(questions)
    resolved_count = len(completed) + len(failed)

    if total_questions > 0 and resolved_count == total_questions:
        return "synthesize"

    return END


# ==================== Allocator to Metrics Collection Routing ====================

def route_from_allocator_to_metrics(state: SystemState) -> Literal["metrics_collection", "__end__"]:
    """
    Check if all tasks are resolved — for allocator comparison experiments.
    """
    questions = state.get("questions", {})
    completed = state.get("completed_tasks", {})
    failed = state.get("failed_tasks", {})

    total_questions = len(questions)
    resolved_count = len(completed) + len(failed)

    if total_questions > 0 and resolved_count == total_questions:
        return "metrics_collection"

    return END
