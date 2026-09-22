from __future__ import annotations

from dataclasses import dataclass

from .llm import LLMClient
from .models import AgentResult, SharedState


@dataclass
class SpecialistAgent:
    name: str
    role: str
    instructions: str
    llm: LLMClient

    def run(self, state: SharedState) -> AgentResult:
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
    return {
        "research": SpecialistAgent("research", "Research Agent", "Investigate the task, identify requirements, facts, assumptions, risks, and useful sources. Do not design the final solution.", llm),
        "developer": SpecialistAgent("developer", "Developer Agent", "Create or revise the concrete solution. Explicitly use research and resolve all review feedback in shared state.", llm),
        "reviewer": SpecialistAgent("reviewer", "Reviewer Agent", "Critically evaluate the proposed solution against the task and research. Set metadata.approved to true only when ready; otherwise return actionable feedback and status needs_revision.", llm),
        "report": SpecialistAgent("report", "Report Agent", "Synthesize the task, research, approved solution, and review into a polished final report. Never report unapproved work as final.", llm),
    }

