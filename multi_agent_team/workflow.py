"""Orchestrate the supervised multi-agent lifecycle and persist its outputs.

``MultiAgentWorkflow`` owns the shared state, repeatedly asks the supervisor
which specialist should run, applies each result, records trace events, and
writes completed workflow artifacts to disk.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

from .agents import build_agents
from .llm import LLMClient
from .models import Event, SharedState
from .supervisor import SupervisorAgent


class MultiAgentWorkflow:
    """Coordinate specialists through a supervisor-controlled shared state."""

    def __init__(self, llm: LLMClient, max_steps: int = 12, on_event: Callable[[Event], None] | None = None):
        """Build a workflow around one model provider.

        Args:
            llm: Provider shared by the supervisor and all specialists.
            max_steps: Maximum supervisor iterations before aborting the run.
            on_event: Optional callback invoked whenever a trace event is added.
        """

        self.supervisor = SupervisorAgent(llm)
        self.agents = build_agents(llm)
        self.max_steps = max_steps
        self.on_event = on_event

    def run(self, task: str) -> SharedState:
        """Run a task until the supervisor finishes or the step limit is hit.

        Each iteration records the supervisor's decision, executes the selected
        specialist, applies its artifact to shared state, and records the result.

        Args:
            task: Natural-language objective for the agent team.

        Returns:
            Completed shared state containing an approved final report.

        Raises:
            RuntimeError: If the supervisor does not finish within ``max_steps``.
            ValueError: If the supervisor proposes an invalid routing decision.
        """

        state = SharedState(task=task)
        for step in range(1, self.max_steps + 1):
            decision = self.supervisor.route(state)
            if decision.next_agent == "finish":
                self._record(state, step, "supervisor", decision.reason)
                return state

            state.current_instruction = decision.instruction
            self._record(state, step, "supervisor", f"Routes to {decision.next_agent}: {decision.reason}")
            result = self.agents[decision.next_agent].run(state)
            self._apply_result(state, decision.next_agent, result)
            self._record(state, step, decision.next_agent, result.summary)

        raise RuntimeError(f"Workflow did not finish within {self.max_steps} steps")

    def _record(self, state: SharedState, step: int, agent: str, summary: str) -> None:
        """Append a trace event and notify the optional observer callback.

        Args:
            state: Shared state whose event list receives the new record.
            step: One-based workflow iteration number.
            agent: Name of the component responsible for the event.
            summary: Human-readable description of what occurred.
        """

        event = Event(step=step, agent=agent, summary=summary)
        state.events.append(event)
        if self.on_event:
            self.on_event(event)

    @staticmethod
    def _apply_result(state: SharedState, agent: str, result) -> None:
        """Merge a specialist result into the appropriate shared-state fields.

        Developer output invalidates any previous review, while a rejected
        review increments the revision counter. Reporting stores the final
        artifact without altering earlier evidence.

        Args:
            state: Shared state to update in place.
            agent: Specialist name that produced ``result``.
            result: Validated result containing an artifact and review metadata.
        """

        if agent == "research":
            state.research = result.artifact
        elif agent == "developer":
            state.solution = result.artifact
            state.review = ""
            state.approved = False
        elif agent == "reviewer":
            state.review = result.artifact
            state.approved = result.metadata.approved and result.status == "completed"
            if not state.approved:
                state.revision_count += 1
        elif agent == "report":
            state.final_report = result.artifact

    @staticmethod
    def save(state: SharedState, output_dir: str | Path) -> None:
        """Persist workflow state, final report, and execution trace.

        The output directory and missing parents are created automatically.
        Existing files with the standard artifact names are replaced.

        Args:
            state: Completed or partial workflow state to serialize.
            output_dir: Destination directory for the three artifact files.
        """

        path = Path(output_dir)
        path.mkdir(parents=True, exist_ok=True)
        (path / "state.json").write_text(state.model_dump_json(indent=2), encoding="utf-8")
        (path / "final_report.md").write_text(state.final_report, encoding="utf-8")
        trace = "\n".join(f"{e.step}. **{e.agent}** — {e.summary}" for e in state.events)
        (path / "execution_trace.md").write_text("# Execution Trace\n\n" + trace + "\n", encoding="utf-8")
