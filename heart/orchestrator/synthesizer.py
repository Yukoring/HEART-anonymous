"""
HEART Synthesizer — Raw Q&A Formatter (Stage 4)

Formats completed Q&A reasoning results into raw text for the SynthesisAgent.
This is a lightweight text formatter (no LLM call) that extracts questions
and answers from the pipeline state, including partial answers from failed tasks.

The formatted text is then passed to SynthesisAgent (agents/synthesis_agent.py),
which uses an LLM to cross-validate answers, resolve contradictions, classify
feasible/infeasible objects, and produce clean constraints for the planner.
"""

from typing import Dict, Any, Optional


class Synthesizer:
    """
    Stage 4 of HEART pipeline.

    Does NOT call a planner — only formats Q&A results into
    heart_constraints_text. The planner is external and pluggable.

    Usage:
        # After HEART reasoning (Stages 1-3)
        constraints = Synthesizer.format_constraints(state)

        # Pass to any planner
        plan = llm_cot_planner.plan(instruction, env_data, heart_constraints=constraints)
        plan = delta_planner.plan(instruction, scene_graph, heart_constraints=constraints)
    """

    @staticmethod
    def format_constraints(state: Dict[str, Any]) -> str:
        """
        Format completed Q&A results into constraints text for planners.

        Args:
            state: SystemState with questions, completed_tasks, failed_tasks

        Returns:
            Formatted Q&A text string (empty string if no results)
        """
        questions = state.get("questions", {})
        completed_tasks = state.get("completed_tasks", {})
        failed_tasks = state.get("failed_tasks", {})

        if not completed_tasks and not failed_tasks:
            return ""

        lines = []

        # Process completed tasks
        for q_id, answer_data in completed_tasks.items():
            question_data = questions.get(q_id, {})
            prompt = question_data.get("prompt", "")
            answer = answer_data.get("answer", "")

            if not answer or answer == "N/A":
                continue

            # Extract clean question
            prompt = _clean_prompt(prompt)

            lines.append(f"Q: {prompt}")
            lines.append(f"A: {answer}\n")

        # Process failed tasks with partial information
        if failed_tasks:
            lines.append("# Incomplete Reasoning:")
            for q_id, failed_data in failed_tasks.items():
                original_prompt = failed_data.get("original_prompt", "")

                base_question = original_prompt.split("Previous attempt")[0].strip()
                if "Question:" in base_question:
                    base_question = base_question.split("Question:")[-1].strip()

                # Extract last partial answer if exists
                if "Previous attempt by " in original_prompt:
                    last_attempt = original_prompt.split("Previous attempt by ")[-1]
                    if ":" in last_attempt and "\n" in last_attempt:
                        partial = last_attempt.split(":", 1)[1]
                        if partial and partial != "N/A":
                            lines.append(f"Q: {base_question}")
                            lines.append(f"A (partial): {partial}\n")
                            continue

                lines.append(f"Q: {base_question}")
                lines.append(f"A: [unavailable]\n")

        if lines:
            return "\n".join(lines)

        return ""


def _clean_prompt(prompt: str) -> str:
    """Clean up prompt text — extract core question only."""
    # Remove "Question:" prefix
    if "Question:" in prompt:
        prompt = prompt.split("Question:")[-1].strip()

    # Remove multi-line metadata (Previous attempt, Additional needed)
    if "\n" in prompt:
        for line in prompt.split("\n"):
            line = line.strip()
            if line and not line.startswith("Previous attempt") and not line.startswith("Additional needed"):
                return line

    return prompt.strip()
