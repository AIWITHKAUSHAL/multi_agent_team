"""Expose the package's public interface for running multi-agent workflows.

Importing :class:`MultiAgentWorkflow` here lets callers use
``from multi_agent_team import MultiAgentWorkflow`` without knowing the module
that contains the implementation.
"""

from .workflow import MultiAgentWorkflow

__all__ = ["MultiAgentWorkflow"]
