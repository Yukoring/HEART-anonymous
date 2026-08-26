"""
Demonstration library for Triple-S, with the paper's top-k retrieval.

Each entry carries a task description, a thought, and an example action
sequence. The description is the retrieval key: minimal tasks from Stage 1 are
embedded and matched against it by cosine similarity, and the k nearest entries
go into the Solution LLM's context (Sec. IV-B).

Stage 4 adds entries during a run. New ones whose description is too close to an
existing entry replace it rather than accumulating alongside it, which is the
paper's guard against Stage 2 retrieving outdated demonstrations.

The seed entries mirror the single worked example the DELTA planner receives, so
that neither method starts with more in-context exposure than the other.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

# Paper's retrieval encoder. HEART's allocator uses a different one; keeping them
# separate leaves each method with the encoder its own authors chose.
RETRIEVAL_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Above this cosine similarity a new demonstration is treated as the same task
# category as an existing one, and replaces it.
REPLACE_THRESHOLD = 0.9


@dataclass
class Demonstration:
    description: str
    thought: str
    actions: List[str]

    def render(self) -> str:
        body = "\n".join(self.actions)
        return (f"[task description] {self.description}\n"
                f"[thought] {self.thought}\n"
                f"[examples]\n{body}")


SEED_DEMONSTRATIONS = [
    Demonstration(
        description="Move an object to a surface in another room",
        thought=("The robot must be in the object's room to pick it up and in the "
                 "destination room to place it, so navigation brackets the pick."),
        actions=[
            "navigate(robot, kitchen_11)",
            "pick(robot, apple_62)",
            "navigate(robot, dining_room_9)",
            "place(robot, apple_62, table_1)",
        ],
    ),
    Demonstration(
        description="Put an object inside a closed container",
        thought=("A container must be open before anything goes in, and the robot "
                 "cannot open it while holding something, so it opens first."),
        actions=[
            "navigate(robot, kitchen_11)",
            "open(robot, dishwasher_20)",
            "pick(robot, bowl_63)",
            "place(robot, bowl_63, dishwasher_20)",
            "close(robot, dishwasher_20)",
        ],
    ),
    Demonstration(
        description="Switch an appliance on after loading it",
        thought=("Turning on happens last and requires the appliance closed and "
                 "the gripper empty."),
        actions=[
            "close(robot, oven_24)",
            "turn_on(robot, oven_24)",
        ],
    ),
]


class DemonstrationLibrary:
    """Top-k retrieval over demonstrations, with the Stage 4 update rule."""

    def __init__(self, seed: Optional[List[Demonstration]] = None,
                 model_name: str = RETRIEVAL_MODEL):
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name, device="cpu")
        self.entries: List[Demonstration] = list(
            SEED_DEMONSTRATIONS if seed is None else seed)
        self._embeddings = self._encode([e.description for e in self.entries])

    def _encode(self, texts: List[str]):
        return self.model.encode(texts, convert_to_tensor=True,
                                 normalize_embeddings=True)

    def retrieve(self, query: str, k: int = 2) -> List[Demonstration]:
        """The k entries whose descriptions are closest to `query`."""
        from sentence_transformers import util

        if not self.entries:
            return []
        scores = util.cos_sim(self._encode([query]), self._embeddings)[0]
        order = scores.argsort(descending=True)[:k]
        return [self.entries[int(i)] for i in order]

    def update(self, demonstration: Demonstration) -> str:
        """
        Add a demonstration, replacing a near-duplicate if one exists.

        Returns "added" or "replaced", which the planner records so the run log
        shows how much the library actually moved.
        """
        from sentence_transformers import util

        if self.entries:
            scores = util.cos_sim(self._encode([demonstration.description]),
                                  self._embeddings)[0]
            best = int(scores.argmax())
            if float(scores[best]) >= REPLACE_THRESHOLD:
                self.entries[best] = demonstration
                self._embeddings = self._encode([e.description for e in self.entries])
                return "replaced"

        self.entries.append(demonstration)
        self._embeddings = self._encode([e.description for e in self.entries])
        return "added"

    def render(self, demonstrations: List[Demonstration]) -> str:
        if not demonstrations:
            return "(none)"
        return "\n\n".join(d.render() for d in demonstrations)
