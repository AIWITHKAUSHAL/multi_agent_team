"""Verify successful, revision, persistence, and unsafe-routing workflows."""

import json
import unittest

from multi_agent_team.llm import DemoClient
from multi_agent_team.models import AgentResult, RouteDecision, SharedState
from multi_agent_team.supervisor import SupervisorAgent
from multi_agent_team.workflow import MultiAgentWorkflow


class RejectOnceClient(DemoClient):
    """Demo provider that rejects the first reviewer call to test revision flow."""

    def __init__(self):
        """Initialize demo state and the number of completed review calls."""

        super().__init__()
        self.reviews = 0

    def structured(self, *, system, prompt, schema):
        """Return one failed review, then delegate all responses to DemoClient."""

        if "ROLE: Reviewer Agent" in system:
            self.reviews += 1
            if self.reviews == 1:
                return schema.model_validate(
                    AgentResult(
                        summary="Missing measurable success criteria.",
                        artifact="REJECTED: Add concrete success metrics.",
                        status="needs_revision",
                        metadata={"approved": False},
                    ).model_dump()
                )
        return super().structured(system=system, prompt=prompt, schema=schema)


class UnsafeClient(DemoClient):
    """Demo provider that deliberately proposes an invalid supervisor route."""

    def structured(self, *, system, prompt, schema):
        """Attempt to route directly to reporting so validation can be tested."""

        if "ROLE: Supervisor Agent" in system:
            return schema.model_validate(
                RouteDecision(next_agent="report", reason="skip review", instruction="report now").model_dump()
            )
        return super().structured(system=system, prompt=prompt, schema=schema)


class WorkflowTests(unittest.TestCase):
    """Exercise the complete workflow and its protected routing invariants."""

    def test_complete_offline_workflow(self):
        """A demo run should create, approve, and persist every artifact."""

        from pathlib import Path

        state = MultiAgentWorkflow(DemoClient()).run("Design a campus recycling campaign")
        self.assertTrue(state.research)
        self.assertTrue(state.solution)
        self.assertTrue(state.approved)
        self.assertTrue(state.final_report.startswith("# Final Report"))
        routed = [e.summary for e in state.events if e.agent == "supervisor"]
        for agent in ("research", "developer", "reviewer", "report"):
            self.assertTrue(any(agent in event for event in routed))

        path = Path("run_output/test_artifacts")
        MultiAgentWorkflow.save(state, path)
        self.assertTrue(json.loads((path / "state.json").read_text())["approved"])
        self.assertTrue((path / "final_report.md").exists())
        self.assertTrue((path / "execution_trace.md").exists())

    def test_rejected_review_routes_back_to_developer(self):
        """A rejected review should trigger revision and a second review."""

        state = MultiAgentWorkflow(RejectOnceClient()).run("Design a campus recycling campaign")
        agents = [event.agent for event in state.events if event.agent != "supervisor"]
        self.assertEqual(agents, ["research", "developer", "reviewer", "developer", "reviewer", "report"])
        self.assertEqual(state.revision_count, 1)
        self.assertTrue(state.approved)

    def test_supervisor_cannot_report_unapproved_work(self):
        """The supervisor must reject reporting before reviewer approval."""

        with self.assertRaisesRegex(ValueError, "before reviewer approval"):
            SupervisorAgent(UnsafeClient()).route(SharedState(task="test"))


if __name__ == "__main__":
    unittest.main()
