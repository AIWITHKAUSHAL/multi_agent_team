"""Define validated data exchanged throughout the multi-agent workflow.

These Pydantic models form the shared contract between the supervisor,
specialists, persistence layer, and LLM structured-output APIs.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

AgentName = Literal["research", "developer", "reviewer", "report", "finish"]


class RouteDecision(BaseModel):
    """Describe which agent the supervisor selected and why."""

    next_agent: AgentName
    reason: str
    instruction: str = ""


class AgentMetadata(BaseModel):
    """Fixed-shape metadata compatible with Gemini's structured-output schema."""

    approved: bool = False


class AgentResult(BaseModel):
    """Represent a specialist's artifact, summary, and review metadata."""

    summary: str
    artifact: str
    status: Literal["completed", "needs_revision"] = "completed"
    metadata: AgentMetadata = Field(default_factory=AgentMetadata)


class Event(BaseModel):
    """Record one timestamped action in the workflow execution trace."""

    step: int
    agent: str
    summary: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SharedState(BaseModel):
    """Hold the task and all artifacts accumulated during a workflow run.

    The state is passed to every agent and mutated by the workflow as research,
    solutions, reviews, approvals, and the final report become available.
    """

    task: str
    research: str = ""
    solution: str = ""
    review: str = ""
    final_report: str = ""
    approved: bool = False
    revision_count: int = 0
    current_instruction: str = ""
    events: list[Event] = Field(default_factory=list)

    def compact_context(self) -> str:
        """Serialize agent-relevant state as readable JSON without event logs.

        Returns:
            An indented JSON snapshot suitable for inclusion in LLM prompts.
        """

        return self.model_dump_json(indent=2, exclude={"events"})
