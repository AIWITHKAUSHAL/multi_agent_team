from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

from .agents import build_agents
from .llm import LLMClient
from .models import Event, SharedState
from .supervisor import SupervisorAgent


class MultiAgentWorkflow:
    def __init__(self, llm: LLMClient, max_steps: int = 12, on_event: Callable[[Event], None] | None = None):
        self.supervisor = SupervisorAgent(llm)
        self.agents = build_agents(llm)
        self.max_steps = max_steps
        self.on_event = on_event

    def run(self, task: str) -> SharedState:
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
        event = Event(step=step, agent=agent, summary=summary)
        state.events.append(event)
        if self.on_event:
            self.on_event(event)

    @staticmethod
    def _apply_result(state: SharedState, agent: str, result) -> None:
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
        path = Path(output_dir)
        path.mkdir(parents=True, exist_ok=True)
        (path / "state.json").write_text(state.model_dump_json(indent=2), encoding="utf-8")
        (path / "final_report.md").write_text(state.final_report, encoding="utf-8")
        trace = "\n".join(f"{e.step}. **{e.agent}** — {e.summary}" for e in state.events)
        (path / "execution_trace.md").write_text("# Execution Trace\n\n" + trace + "\n", encoding="utf-8")
