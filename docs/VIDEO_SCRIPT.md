# Video walkthrough script (about 5–7 minutes)

## 1. Introduce the goal (30 seconds)

“This project coordinates five specialized agents to complete one larger task. It uses Gemini 3.5 Flash-Lite, dynamic supervisor routing, and persistent shared state.” Show the README requirements table.

## 2. Explain the architecture (60–90 seconds)

Show `docs/architecture.svg`. Explain that the user task enters the Supervisor, which chooses only one next agent. Every agent reads and updates the central `SharedState`. Point out the rejection arrow: a Reviewer can cause another Developer pass, so this is not merely five sequential calls.

## 3. Connect diagram to code (2 minutes)

- Open `models.py`: show `SharedState`, `RouteDecision`, and `AgentResult`.
- Open `supervisor.py`: show the choices, state-based prompt, and approval guardrails.
- Open `agents.py`: show the distinct Research, Developer, Reviewer, and Report roles.
- Open `workflow.py`: show the loop, one selected agent per iteration, state mutation, and event log.
- Open `llm.py`: show `gemini-3.5-flash-lite`, JSON schema responses, and API key loading.

## 4. Execute a complete task (2 minutes)

Run:

```powershell
multi-agent "Create a practical plan to reduce food waste in a university cafeteria"
```

Narrate each console route. Open `run_output/state.json` and show that downstream agents received upstream artifacts. Open `execution_trace.md` and `final_report.md`.

If you do not want to spend API quota during rehearsal, add `--demo`. Use the real Gemini run in the submitted recording.

## 5. Demonstrate dynamic revision (45 seconds)

Run `python -m unittest discover -s tests -v`. Explain that `test_rejected_review_routes_back_to_developer` scripts a failed review and asserts the route contains Developer → Reviewer → Developer → Reviewer. This proves routing supports feedback loops rather than blindly invoking every agent once.

## 6. Close (20 seconds)

Show the GitHub URL and confirm it points to the exact folder. Mention that `.env` is ignored, the repository contains `.env.example`, and the YouTube video is Public or Unlisted.
