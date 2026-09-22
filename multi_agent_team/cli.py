from __future__ import annotations

import argparse
import os

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

from .llm import DemoClient, GeminiClient
from .workflow import MultiAgentWorkflow


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Run the Gemini multi-agent team")
    parser.add_argument("task", nargs="?", default="Create a practical plan to reduce food waste in a university cafeteria.")
    parser.add_argument("--demo", action="store_true", help="Run offline with deterministic model responses")
    parser.add_argument("--output", default="run_output", help="Directory for state, trace, and final report")
    parser.add_argument("--max-steps", type=int, default=int(os.getenv("MAX_STEPS", "12")))
    args = parser.parse_args()

    console = Console()
    if not args.demo and not (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")):
        parser.error("GOOGLE_API_KEY is required in .env (or use --demo)")
    llm = DemoClient() if args.demo else GeminiClient()

    def show(event):
        console.print(f"[bold cyan]Step {event.step} · {event.agent}[/bold cyan]  {event.summary}")

    state = MultiAgentWorkflow(llm, max_steps=args.max_steps, on_event=show).run(args.task)
    MultiAgentWorkflow.save(state, args.output)
    console.print(Panel(state.final_report, title="Final Report", border_style="green"))
    console.print(f"Artifacts saved to [bold]{args.output}[/bold]")


if __name__ == "__main__":
    main()
