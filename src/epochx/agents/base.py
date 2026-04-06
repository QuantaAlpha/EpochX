"""AgentDriver ABC — extracted from FeatureBench BaseAgent pattern.

This is the base for full-auto mode (Phase 3). Each agent driver defines how
to install, configure, and run an AI agent inside a Docker container.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class AgentDriver(ABC):
    """Base class for agent drivers (full-auto mode)."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Agent identifier, e.g., 'claude-code'."""
        ...

    @property
    @abstractmethod
    def install_script(self) -> str:
        """Shell script to install the agent inside a container."""
        ...

    @abstractmethod
    def get_run_command(self, prompt: str, model: str | None = None) -> str:
        """Command to execute the agent with a given prompt."""
        ...

    def get_env_setup_script(self, env_vars: dict[str, str] | None = None) -> str:
        """Environment variable setup script."""
        lines = []
        for k, v in (env_vars or {}).items():
            lines.append(f"export {k}={v}")
        return "\n".join(lines)

    def pre_run_hook(self, workspace_path: str) -> bool:
        """Called before agent execution. Return False to abort."""
        return True

    def post_run_hook(self, workspace_path: str, log: str) -> bool:
        """Called after agent execution. Return True if successful."""
        return True


# --- Registry ---

_AGENT_REGISTRY: dict[str, type[AgentDriver]] = {}


def register_agent(cls: type[AgentDriver]) -> type[AgentDriver]:
    """Decorator: register an AgentDriver subclass."""
    instance = cls()
    _AGENT_REGISTRY[instance.name] = cls
    return cls


def get_agent(name: str) -> AgentDriver:
    """Instantiate a registered agent driver by name."""
    if name not in _AGENT_REGISTRY:
        available = ", ".join(sorted(_AGENT_REGISTRY.keys()))
        raise ValueError(f"Unknown agent: {name}. Available: {available}")
    return _AGENT_REGISTRY[name]()


def list_agents() -> list[str]:
    """List all registered agent driver names."""
    return sorted(_AGENT_REGISTRY.keys())
