"""
Basic test — runs HEART pipeline on a single task to verify setup.
Usage: python heart/tests/test_basic.py
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Paths relative to project root (heart/tests/ → heart/ → HEART/)
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCENE_PATH = PROJECT_ROOT / "data" / "scenes" / "Tiny_Benevolence_1_scene_graph.json"
URDF_PATH = PROJECT_ROOT / "data" / "robots" / "fetch_gripper.urdf"


def load_env_data():
    """Load scene graph and robot URDF, build env_data dict."""
    from heart.utils.urdf_parser import parse_urdf_to_specs

    # Load scene graph
    with open(SCENE_PATH, "r") as f:
        scene_graph = json.load(f)

    # Parse URDF
    robot_specs = parse_urdf_to_specs(str(URDF_PATH))

    # Build env_data
    env_data = {
        "scene_graph": scene_graph,
        "robots": {
            "robot": {
                "urdf": robot_specs,
                "position": [-0.5, -6.0, 0.0],
                "location": [],
                "state": [],
                "capability": [],
            }
        },
    }
    return env_data


def test_imports():
    """Test that all imports work."""
    print("Testing imports...")
    from heart.core.schema import AgentType, TaskType, AgentResponse
    from heart.core.state import initialize_state, StageType
    from heart.configs.models import REASONING_AGENTS
    from heart.agents import ReasoningAgent
    from heart.orchestrator.synthesizer import Synthesizer
    from heart.workflows.workflow import create_workflow
    from planners.llm_cot import LLMCoTPlanner
    print("  All imports OK")


def test_state_initialization():
    """Test state creation with different agent configs."""
    from heart.core.state import initialize_state

    print("Testing state initialization...")

    # 5 agents
    agents_5 = ["capability_reasoner", "environmental_reasoner", "path_reasoner",
                 "feasibility_reasoner", "constraint_reasoner"]
    state = initialize_state(
        instruction="Test instruction",
        env_data={"scene_graph": {}, "robots": {}},
        agents=agents_5,
        planner_type="llm_cot",
    )
    assert len(state["agent_capacities"]) == 5
    assert state["planner_type"] == "llm_cot"
    print(f"  5 agents: OK (capacities: {state['agent_capacities']})")

    # 1 agent
    state = initialize_state(
        instruction="Test",
        env_data={},
        agents=["homogeneous_reasoner"],
        planner_type=None,
    )
    assert len(state["agent_capacities"]) == 1
    assert state["planner_type"] is None
    print(f"  1 agent: OK (capacities: {state['agent_capacities']})")


def test_agent_creation():
    """Test ReasoningAgent creation with data filtering."""
    from heart.agents import ReasoningAgent

    print("Testing agent creation...")
    env_data = load_env_data()

    # Create capability agent
    agent = ReasoningAgent("capability_reasoner", env_data=env_data)
    print(f"  capability_reasoner: {agent.estimated_tokens} estimated tokens")
    print(f"    filtered data keys: {list(agent.filtered_env_data.keys())}")

    # Create environmental agent
    agent = ReasoningAgent("environmental_reasoner", env_data=env_data)
    print(f"  environmental_reasoner: {agent.estimated_tokens} estimated tokens")
    print(f"    filtered data keys: {list(agent.filtered_env_data.keys())}")

    # Create homogeneous agent (gets all data)
    agent = ReasoningAgent("homogeneous_reasoner", env_data=env_data)
    print(f"  homogeneous_reasoner: {agent.estimated_tokens} estimated tokens")
    print(f"    filtered data keys: {list(agent.filtered_env_data.keys())}")


def test_workflow_creation():
    """Test workflow graph creation with different configs."""
    from heart.workflows.workflow import create_workflow

    print("Testing workflow creation...")

    # 5 agents + llm_cot planner
    agents = ["capability_reasoner", "environmental_reasoner", "path_reasoner",
              "feasibility_reasoner", "constraint_reasoner"]
    wf = create_workflow(agents=agents, allocator_type="heart", planner_type="llm_cot")
    print(f"  5 agents + llm_cot: OK")

    # 1 agent, no planner
    wf = create_workflow(agents=["homogeneous_reasoner"], allocator_type="heart", planner_type=None)
    print(f"  1 agent + no planner: OK")


def test_full_pipeline():
    """
    Full pipeline test — actually calls LLM APIs.
    Only run if OPENAI_API_KEY is set.
    """
    if not os.environ.get("OPENAI_API_KEY"):
        print("Skipping full pipeline test (no OPENAI_API_KEY)")
        return

    from heart.core.state import initialize_state
    from heart.workflows.workflow import create_workflow

    print("Testing full pipeline (LLM calls)...")

    env_data = load_env_data()
    instruction = "Serve food to dining table by putting any one apple and hamburger"

    agents = ["capability_reasoner", "environmental_reasoner", "path_reasoner",
              "feasibility_reasoner", "constraint_reasoner"]

    state = initialize_state(
        instruction=instruction,
        env_data=env_data,
        agents=agents,
        planner_type="llm_cot",
    )

    workflow = create_workflow(
        agents=agents,
        allocator_type="heart",
        planner_type="llm_cot",
    )

    result = workflow.invoke(state, config={"recursion_limit": 100})

    # Check results
    print(f"\n  Completed tasks: {len(result.get('completed_tasks', {}))}")
    print(f"  Failed tasks: {len(result.get('failed_tasks', {}))}")
    print(f"  Constraints text: {len(result.get('heart_constraints_text', ''))} chars")
    print(f"  Plan steps: {len(result.get('plan_steps', []))}")

    if result.get("plan_steps"):
        print(f"\n  Plan:")
        for i, step in enumerate(result["plan_steps"]):
            print(f"    {i+1}. {step}")


if __name__ == "__main__":
    print("=" * 60)
    print("HEART Basic Test")
    print("=" * 60)

    test_imports()
    print()

    test_state_initialization()
    print()

    test_agent_creation()
    print()

    test_workflow_creation()
    print()

    # Uncomment to run full pipeline (costs API tokens)
    # test_full_pipeline()

    print("=" * 60)
    print("All tests passed!")
    print("=" * 60)
