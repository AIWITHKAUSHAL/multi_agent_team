from __future__ import annotations

from .llm import LLMClient
from .models import RouteDecision, SharedState


class SupervisorAgent:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    def route(self, state: SharedState) -> RouteDecision:
        system = """ROLE: Supervisor Agent
Choose exactly one next specialist based on the current shared state, not a fixed sequence.
Available choices: research, developer, reviewer, report, finish.
Routing rules:
- Fill missing evidence with research.
- Use developer to create a solution or address a failed review.
- Use reviewer whenever a new/revised solution needs evaluation.
- Use report only after reviewer approval.
- Use finish only when final_report exists.
Explain why the selected agent is the best next action."""
        decision = self.llm.structured(
            system=system,
            prompt=f"Select the next agent.\nSTATE:\n{state.compact_context()}",
            schema=RouteDecision,
        )
        self._validate(decision, state)
        return decision

    @staticmethod
    def _validate(decision: RouteDecision, state: SharedState) -> None:
        if decision.next_agent == "report" and not state.approved:
            raise ValueError("Supervisor attempted report before reviewer approval")
        if decision.next_agent == "finish" and not state.final_report:
            raise ValueError("Supervisor attempted finish before a final report exists")

