"""Route shared workflow state to the most appropriate specialist agent.

The supervisor asks the configured LLM to choose the next action dynamically,
then enforces workflow invariants before the decision can be executed.
"""

from __future__ import annotations

from .llm import LLMClient
from .models import RouteDecision, SharedState


class SupervisorAgent:
    """LLM-backed coordinator that selects and validates the next workflow step."""

    def __init__(self, llm: LLMClient):
        """Store the language-model provider used to make routing decisions.

        Args:
            llm: Provider capable of returning a structured ``RouteDecision``.
        """

        self.llm = llm

    def route(self, state: SharedState) -> RouteDecision:
        """Choose the next specialist based on the current shared state.

        The routing prompt describes the permitted progression from research to
        an approved final report. The returned decision is validated again in
        code to prevent reporting unapproved work or finishing without output.

        Args:
            state: Current workflow state used to determine what is missing.

        Returns:
            The validated next-agent decision and its tailored instruction.

        Raises:
            ValueError: If the decision violates a protected workflow invariant.
        """

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
        """Reject routing decisions that skip required approval or output.

        Args:
            decision: Supervisor decision proposed by the language model.
            state: Current state against which the decision is checked.

        Raises:
            ValueError: If reporting is selected before approval or finishing is
                selected before a final report exists.
        """

        if decision.next_agent == "report" and not state.approved:
            raise ValueError("Supervisor attempted report before reviewer approval")
        if decision.next_agent == "finish" and not state.final_report:
            raise ValueError("Supervisor attempted finish before a final report exists")
