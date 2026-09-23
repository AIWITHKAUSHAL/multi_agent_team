"""Define specialist agents and assemble the workflow's agent registry.

Each specialist receives the same shared workflow state but is prompted with a
different role. This module translates that state into LLM prompts and returns
validated :class:`~multi_agent_team.models.AgentResult` objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from .llm import LLMClient
from .models import AgentResult, SharedState


@dataclass
class SpecialistAgent:
    """An LLM-backed worker configured to perform one specialist role.

    Attributes:
        name: Registry key used by the supervisor to select the agent.
        role: Human-readable role included in the LLM system instruction.
        instructions: Role-specific constraints and responsibilities.
        llm: Provider used to generate a structured, validated response.
    """

    name: str
    role: str
    instructions: str
    llm: LLMClient

    def run(self, state: SharedState) -> AgentResult:
        """Execute the specialist against the current shared state.

        The method builds role and task prompts containing the supervisor's
        latest instruction and a compact snapshot of all shared artifacts. It
        asks the configured LLM for an ``AgentResult`` so downstream workflow
        code can safely consume a validated response.

        Args:
            state: Current task, artifacts, approval status, and instruction.

        Returns:
            The specialist's validated summary, artifact, status, and metadata.
        """

        system = f"""ROLE: {self.role}
You are one specialist in a supervised multi-agent team.
{self.instructions}
Use the shared state; do not invent another agent's output. Return a concise artifact and summary."""
        prompt = f"""TASK:
{state.task}

SUPERVISOR INSTRUCTION:
{state.current_instruction}

SHARED STATE:
{state.compact_context()}"""
        return self.llm.structured(system=system, prompt=prompt, schema=AgentResult)


def build_agents(llm: LLMClient) -> dict[str, SpecialistAgent]:
    """Create the four specialists available to the supervisor.

    Args:
        llm: Shared language-model provider used by every specialist.

    Returns:
        A mapping from routing names to research, development, review, and
        reporting agents.
    """

    return {
        "research": SpecialistAgent("research", "Research Agent", "Investigate the task, identify requirements, facts, assumptions, risks, and useful sources. Do not design the final solution.", llm),
        "developer": SpecialistAgent("developer", "Developer Agent", "Create or revise the concrete solution. Explicitly use research and resolve all review feedback in shared state.", llm),
        "reviewer": SpecialistAgent("reviewer", "Reviewer Agent", "Critically evaluate the proposed solution against the task and research. Set metadata.approved to true only when ready; otherwise return actionable feedback and status needs_revision.", llm),
        "report": SpecialistAgent("report", "Report Agent", "Synthesize the task, research, approved solution, and review into a polished final report. Never report unapproved work as final.", llm),
    }
