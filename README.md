# Gemini Multi-Agent Team

A dynamically routed, shared-state multi-agent application powered by Google's
`gemini-3.5-flash-lite` model. One Supervisor Agent selects the next action at
runtime while four specialist agents research, develop, review, and report. The
same workflow is available through a command-line interface and a Streamlit web
application.

![Complete runtime flow](docs/app_flow.png)

## Features

- Dynamic routing based on current state instead of a fixed agent sequence
- Structured Pydantic responses for routing decisions and specialist results
- A review gate that prevents unapproved work from reaching the final report
- Automatic revision loops when the Reviewer rejects a solution
- Shared state containing every intermediate artifact and workflow event
- Real Gemini execution and a deterministic, API-key-free demo mode
- CLI and Streamlit interfaces backed by the same workflow implementation
- JSON state, Markdown report, and readable execution-trace output

## How it works

![Multi-agent architecture](docs/architecture.svg)

The team contains one coordinator and four specialists:

| Component | Responsibility |
|---|---|
| Supervisor Agent | Examines `SharedState` and selects exactly one next action |
| Research Agent | Collects requirements, facts, assumptions, risks, and sources |
| Developer Agent | Creates or revises the solution using research and review feedback |
| Reviewer Agent | Approves the solution or returns actionable revision feedback |
| Report Agent | Synthesizes approved work into the final deliverable |

Each workflow iteration follows this cycle:

1. The Supervisor receives a compact JSON representation of the shared state.
2. Gemini returns a validated `RouteDecision`: `research`, `developer`,
   `reviewer`, `report`, or `finish`.
3. The selected specialist reads the task, supervisor instruction, and existing
   artifacts, then returns a validated `AgentResult`.
4. The workflow updates `SharedState` and records an event.
5. The cycle repeats until an approved final report exists.

Code-level guardrails reject a request to run the Report Agent before reviewer
approval and reject `finish` before a final report exists.

For a detailed numbered call chain and state timeline, see the
[runtime-flow image](docs/app_flow.png). All documentation images and their
references are catalogued in [docs/README.md](docs/README.md).

## Requirements

- Python 3.11 or newer
- A Gemini API key for live mode
- No API key is required for demo mode

## Installation

Create and activate a virtual environment.

macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

Install the CLI, test tools, and optional Streamlit interface:

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev,ui]"
```

If only the CLI is needed, install `.[dev]` instead.

## Configuration

Copy the example environment file and add your API key:

macOS or Linux:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Configuration values:

```dotenv
GOOGLE_API_KEY=your_real_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
MAX_STEPS=12
```

`GOOGLE_API_KEY` is preferred, but `GEMINI_API_KEY` is also supported. An
explicit model passed to `GeminiClient` takes precedence over `GEMINI_MODEL`.
Never commit `.env`; only `.env.example` belongs in source control.

## Run the Streamlit web app

Start the application from the repository root:

```bash
streamlit run streamlit_app.py
```

The page opens at `http://localhost:8501`. Enter a task, select live or offline
demo mode, choose the maximum number of steps and output directory, then click
**Run workflow**. The page displays live trace events and separate tabs for the
final report, research, solution, review, and complete state. The final report
can also be downloaded directly from the page.

## Run the CLI

Live Gemini execution:

```bash
multi-agent "Design a verified disaster-response communication plan for a college campus"
```

API-key-free demonstration:

```bash
multi-agent --demo "Create a practical plan to reduce food waste in a university cafeteria"
```

Run without the installed console command:

```bash
python -m multi_agent_team.cli --demo "Your task"
```

CLI options:

| Option | Purpose | Default |
|---|---|---|
| `task` | Natural-language task for the team | Food-waste planning example |
| `--demo` | Use deterministic local responses instead of Gemini | Disabled |
| `--output PATH` | Select the artifact output directory | `run_output` |
| `--max-steps N` | Limit supervisor iterations | `MAX_STEPS` or `12` |

## Output files

Both interfaces call `MultiAgentWorkflow.save()` and produce:

| File | Contents |
|---|---|
| `state.json` | Complete shared state, intermediate artifacts, and event history |
| `execution_trace.md` | Human-readable supervisor decisions and agent handoffs |
| `final_report.md` | Final deliverable produced after reviewer approval |

The default destination is `run_output/`. Use `--output` in the CLI or the
**Output directory** field in Streamlit to choose another location. Existing
files with these names in that location are replaced.

## Project structure

```text
.
├── streamlit_app.py             # Streamlit web interface
├── pyproject.toml               # Package metadata and dependencies
├── .env.example                 # Safe environment-variable template
├── multi_agent_team/
│   ├── __init__.py              # Public package interface
│   ├── agents.py                # Specialist definitions and registry
│   ├── cli.py                   # Command-line entry point
│   ├── llm.py                   # Gemini and offline demo providers
│   ├── models.py                # Typed shared state and structured outputs
│   ├── supervisor.py            # Dynamic router and safety validation
│   └── workflow.py              # Event loop, state updates, and persistence
├── tests/
│   └── test_workflow.py         # Completion, revision, and guardrail tests
└── docs/
    ├── README.md                # Documentation and image reference index
    ├── architecture.svg         # High-level architecture diagram
    ├── app_flow.png             # Detailed runtime-flow illustration
    └── VIDEO_SCRIPT.md          # Suggested project walkthrough
```

## Testing

Run the test suite with either command:

```bash
python -m pytest
python -m unittest discover -s tests -v
```

The tests cover:

- A complete offline workflow and artifact persistence
- Rejection followed by Developer revision and Reviewer re-evaluation
- Prevention of reporting before reviewer approval

For a quick end-to-end smoke test without an API key:

```bash
multi-agent --demo --output run_output "Verify the application workflow"
```

## Troubleshooting

- **Missing API key:** add `GOOGLE_API_KEY` to `.env` or enable demo mode.
- **Workflow reaches its step limit:** increase `--max-steps`, `MAX_STEPS`, or
  the Streamlit **Max steps** value, and inspect `execution_trace.md`.
- **`streamlit` command not found:** install the UI extra with
  `python -m pip install -e ".[ui]"` inside the activated environment.
- **Gemini returns an error:** confirm the key, model name, network access, and
  account quota, then retry in demo mode to verify local orchestration.

## Documentation references

- [Documentation and visual asset index](docs/README.md)
- [Video walkthrough script](docs/VIDEO_SCRIPT.md)
- [Gemini 3.5 Flash-Lite model documentation](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite)
- [Google Gen AI Python SDK quickstart](https://ai.google.dev/gemini-api/docs/quickstart)
