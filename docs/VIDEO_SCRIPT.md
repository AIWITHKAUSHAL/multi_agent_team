# Video walkthrough script (about 5–7 minutes)

## 1. Introduce the goal (30 seconds)

“This project coordinates one Supervisor Agent and four specialist agents to
complete one larger task. It uses Gemini 3.5 Flash-Lite, dynamic supervisor
routing, and persistent shared state.” Show the README introduction and feature
list.

## 2. Explain the architecture (60–90 seconds)

Start with `docs/architecture.svg`. Explain that the user task enters the
Supervisor, which chooses only one next agent. Every specialist reads the
central `SharedState`, and the workflow applies each result to that state. Point
out the rejection arrow: a Reviewer can cause another Developer pass, so this
is not merely a fixed sequence. Then show `docs/app_flow.png` for the numbered
file-to-file call chain and state-update timeline.

## 3. Connect diagram to code (2 minutes)

- Open `models.py`: show `SharedState`, `RouteDecision`, and `AgentResult`.
- Open `supervisor.py`: show the choices, state-based prompt, and approval guardrails.
- Open `agents.py`: show the distinct Research, Developer, Reviewer, and Report roles.
- Open `workflow.py`: show the loop, one selected agent per iteration, state mutation, and event log.
- Open `llm.py`: show `gemini-3.5-flash-lite`, JSON schema responses, and API key loading.

## 4. Execute a complete task (2 minutes)

Choose either the web interface or CLI for the main demonstration.

Streamlit option:

```powershell
streamlit run streamlit_app.py
```

Enter the task, run the workflow, narrate the live routing events, and open the
Final report, Research, Solution, Review, and State JSON tabs.

CLI option:

Run:

```powershell
multi-agent "Create a practical plan to reduce food waste in a university cafeteria"
```

Narrate each console route. Open `run_output/state.json` and show that downstream
agents received upstream artifacts. Open `execution_trace.md` and
`final_report.md`.

If you do not want to spend API quota during rehearsal, add `--demo` to the CLI
or enable **Demo mode (offline)** in Streamlit. Use the real Gemini mode in the
submitted recording when required.

## 5. Demonstrate dynamic revision (45 seconds)

Run `python -m unittest discover -s tests -v`. Explain that `test_rejected_review_routes_back_to_developer` scripts a failed review and asserts the route contains Developer → Reviewer → Developer → Reviewer. This proves routing supports feedback loops rather than blindly invoking every agent once.

## 6. Close (20 seconds)

Show the GitHub URL and confirm it points to the exact folder. Mention that `.env` is ignored, the repository contains `.env.example`, and the YouTube video is Public or Unlisted.
