from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

AgentName = Literal["research", "developer", "reviewer", "report", "finish"]


class RouteDecision(BaseModel):
    next_agent: AgentName
    reason: str
    instruction: str = ""


class AgentMetadata(BaseModel):
    """Fixed-shape metadata compatible with Gemini's structured-output schema."""

    approved: bool = False


class AgentResult(BaseModel):
    summary: str
    artifact: str
    status: Literal["completed", "needs_revision"] = "completed"
    metadata: AgentMetadata = Field(default_factory=AgentMetadata)


class Event(BaseModel):
    step: int
    agent: str
    summary: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SharedState(BaseModel):
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
        return self.model_dump_json(indent=2, exclude={"events"})
