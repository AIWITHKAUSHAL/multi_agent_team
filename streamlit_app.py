"""Provide a Streamlit web UI for running the multi-agent workflow.

Run with ``streamlit run streamlit_app.py``. The page mirrors the CLI: pick
Gemini or the offline demo provider, enter a task, watch trace events stream
in, then inspect the final report and intermediate artifacts.
"""

from __future__ import annotations

import os

import streamlit as st
from dotenv import load_dotenv

from multi_agent_team.llm import DemoClient, GeminiClient
from multi_agent_team.workflow import MultiAgentWorkflow

load_dotenv()

st.set_page_config(page_title="Gemini Multi-Agent Team", layout="wide")
st.title("Gemini Multi-Agent Team")

has_key = bool(os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"))

with st.sidebar:
    demo = st.toggle("Demo mode (offline)", value=not has_key)
    max_steps = st.number_input("Max steps", min_value=1, max_value=50, value=int(os.getenv("MAX_STEPS", "12")))
    output_dir = st.text_input("Output directory", value="run_output")
    if not demo and not has_key:
        st.error("GOOGLE_API_KEY is missing from .env. Add it or enable demo mode.")

task = st.text_area(
    "Task",
    value="Create a practical plan to reduce food waste in a university cafeteria.",
    height=100,
)

if st.button("Run workflow", type="primary", disabled=not task.strip() or (not demo and not has_key)):
    llm = DemoClient() if demo else GeminiClient()
    status = st.status("Running agents…", expanded=True)

    def show(event):
        """Render a single workflow event inside the status panel."""

        status.write(f"**Step {event.step} · {event.agent}** — {event.summary}")

    try:
        state = MultiAgentWorkflow(llm, max_steps=int(max_steps), on_event=show).run(task.strip())
    except Exception as exc:  # surface provider and routing errors in the UI
        status.update(label="Workflow failed", state="error")
        st.exception(exc)
        st.stop()

    status.update(label="Workflow complete", state="complete", expanded=False)
    MultiAgentWorkflow.save(state, output_dir)
    st.caption(f"Artifacts saved to `{output_dir}`")

    report_tab, research_tab, solution_tab, review_tab, state_tab = st.tabs(
        ["Final report", "Research", "Solution", "Review", "State JSON"]
    )
    with report_tab:
        st.markdown(state.final_report)
        st.download_button("Download report", state.final_report, file_name="final_report.md")
    with research_tab:
        st.markdown(state.research or "_No research produced._")
    with solution_tab:
        st.markdown(state.solution or "_No solution produced._")
    with review_tab:
        st.markdown(state.review or "_No review produced._")
        st.write(f"Approved: **{state.approved}** · Revisions: **{state.revision_count}**")
    with state_tab:
        st.json(state.model_dump())
