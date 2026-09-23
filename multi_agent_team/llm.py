"""Define structured LLM providers used by supervisors and specialists.

The abstract interface keeps workflow code independent of a particular model.
``GeminiClient`` performs real Gemini requests, while ``DemoClient`` provides
predictable local responses for tests and API-key-free demonstrations.
"""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMClient(ABC):
    """Interface for model providers that return Pydantic-validated data."""

    @abstractmethod
    def structured(self, *, system: str, prompt: str, schema: type[T]) -> T:
        """Generate a response and validate it against ``schema``.

        Args:
            system: High-level role, behavior, and response instructions.
            prompt: Task-specific input sent to the model.
            schema: Pydantic model class describing the required output shape.

        Returns:
            An instance of ``schema`` containing the validated model response.
        """


class GeminiClient(LLMClient):
    """Production provider that requests structured output from Gemini."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        """Configure the Gemini SDK client and model.

        Explicit arguments take precedence over environment variables. The API
        key falls back to ``GOOGLE_API_KEY`` and then ``GEMINI_API_KEY``; the
        model falls back to ``GEMINI_MODEL`` and finally the project default.

        Args:
            api_key: Optional Gemini API key override.
            model: Optional Gemini model-name override.
        """

        from google import genai

        self.model = model or os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
        resolved_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=resolved_key)

    def structured(self, *, system: str, prompt: str, schema: type[T]) -> T:
        """Request JSON from Gemini and return it as a validated model.

        Gemini is instructed to conform to the supplied Pydantic schema. The
        SDK's parsed response is used when available; otherwise the raw response
        text is parsed and validated locally.

        Args:
            system: System instruction controlling model behavior.
            prompt: User content for the current model call.
            schema: Pydantic class required for the response.

        Returns:
            A validated instance of ``schema``.
        """

        from google.genai import types

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system,
                response_mime_type="application/json",
                response_schema=schema,
                temperature=0.2,
            ),
        )
        if getattr(response, "parsed", None) is not None:
            parsed = response.parsed
            return parsed if isinstance(parsed, schema) else schema.model_validate(parsed)
        return schema.model_validate_json(response.text)


class DemoClient(LLMClient):
    """Deterministic local provider used for evaluation and API-key-free demos."""

    def __init__(self):
        """Initialize the counter used to track local model calls."""

        self.calls = 0

    def structured(self, *, system: str, prompt: str, schema: type[T]) -> T:
        """Return deterministic routing decisions or specialist artifacts.

        Supervisor calls are detected from the requested schema and routed by
        inspecting serialized shared state. Specialist calls are detected from
        the role in the system prompt. Every generated dictionary is validated
        through ``schema`` to mirror the production provider's contract.

        Args:
            system: Role instructions used to identify specialist calls.
            prompt: Prompt containing the task or serialized workflow state.
            schema: Pydantic class used to validate the local response.

        Returns:
            A deterministic, validated instance of ``schema``.
        """

        self.calls += 1
        fields = schema.model_fields
        if "next_agent" in fields:
            state = json.loads(prompt.split("STATE:\n", 1)[1])
            if not state["research"]:
                data = {"next_agent": "research", "reason": "Evidence is missing", "instruction": "Gather requirements, facts, and constraints."}
            elif not state["solution"] or (not state["approved"] and state["review"]):
                data = {"next_agent": "developer", "reason": "A solution or revision is needed", "instruction": "Build or revise using research and review feedback."}
            elif not state["review"]:
                data = {"next_agent": "reviewer", "reason": "The solution needs independent quality review", "instruction": "Check completeness, correctness, and risks."}
            elif state["approved"] and not state["final_report"]:
                data = {"next_agent": "report", "reason": "Approved work is ready for synthesis", "instruction": "Produce the final deliverable."}
            else:
                data = {"next_agent": "finish", "reason": "The final report is complete", "instruction": ""}
            return schema.model_validate(data)

        role = system.split("ROLE:", 1)[-1].splitlines()[0].strip()
        task = prompt.split("TASK:\n", 1)[-1].split("\n\n", 1)[0]
        if role == "Research Agent":
            artifact = f"Research brief for: {task}\n- Define audience and success criteria.\n- Validate assumptions and constraints.\n- Prefer testable, cited evidence in production."
            data = {"summary": "Collected requirements and supporting considerations.", "artifact": artifact}
        elif role == "Developer Agent":
            artifact = f"Proposed solution for: {task}\n1. Use the research brief as requirements.\n2. Implement a clear, testable deliverable.\n3. Address every reviewer concern before release."
            data = {"summary": "Created a solution grounded in the shared research.", "artifact": artifact}
        elif role == "Reviewer Agent":
            data = {"summary": "The solution covers the task and is internally consistent.", "artifact": "APPROVED\nChecks: requirements, clarity, feasibility, and traceability passed.", "metadata": {"approved": True}}
        else:
            artifact = f"# Final Report\n\n## Objective\n{task}\n\n## Evidence\nResearch and solution artifacts were reviewed.\n\n## Recommendation\nProceed with the approved solution recorded in shared state."
            data = {"summary": "Synthesized the approved artifacts into a final report.", "artifact": artifact}
        return schema.model_validate(data)
