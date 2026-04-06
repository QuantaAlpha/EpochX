"""Persistent task and environment state management."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class EnvironmentState:
    """Runtime environment state for a task."""

    task_id: str
    benchmark: str
    workspace: str
    status: str  # "running"|"collecting"|"grading"|"completed"|"failed"|"stopped"
    container_id: str | None = None
    ssh_port: int | None = None
    ssh_host: str | None = None
    container_workdir: str | None = None
    runtime: str = "host"
    started_at: str = ""
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.started_at:
            self.started_at = datetime.now(timezone.utc).isoformat()


class StateManager:
    """Manages persistent task and environment state."""

    def __init__(self, state_file: Path | None = None):
        if state_file is None:
            state_file = Path.home() / ".epochx" / "state.json"
        self._state_file = state_file
        self._state_file.parent.mkdir(parents=True, exist_ok=True)

    def save_environment(self, env: EnvironmentState) -> None:
        """Save or update an environment state."""
        state = self._load()
        state.setdefault("environments", {})[env.task_id] = asdict(env)
        self._save(state)

    def get_environment(self, task_id: str) -> EnvironmentState | None:
        """Get environment state by task ID."""
        state = self._load()
        data = state.get("environments", {}).get(task_id)
        if data is None:
            return None
        return EnvironmentState(**data)

    def update_status(self, task_id: str, status: str) -> None:
        """Update the status of an environment."""
        state = self._load()
        envs = state.get("environments", {})
        if task_id in envs:
            envs[task_id]["status"] = status
            self._save(state)

    def list_environments(
        self, status: str | None = None
    ) -> list[EnvironmentState]:
        """List all environments, optionally filtered by status."""
        state = self._load()
        envs = state.get("environments", {})
        result = []
        for data in envs.values():
            if status is None or data.get("status") == status:
                result.append(EnvironmentState(**data))
        return result

    def remove_environment(self, task_id: str) -> None:
        """Remove an environment state."""
        state = self._load()
        envs = state.get("environments", {})
        if task_id in envs:
            del envs[task_id]
            self._save(state)

    def save_result(self, task_id: str, result: dict) -> None:
        """Save evaluation result for a task."""
        state = self._load()
        state.setdefault("results", {})[task_id] = result
        self._save(state)

    def get_results(self, benchmark: str | None = None) -> dict:
        """Get results, optionally filtered by benchmark."""
        state = self._load()
        results = state.get("results", {})
        if benchmark is None:
            return results
        return {
            k: v
            for k, v in results.items()
            if v.get("benchmark") == benchmark
        }

    def _load(self) -> dict:
        """Load state from JSON file."""
        if not self._state_file.exists():
            return {}
        try:
            return json.loads(self._state_file.read_text())
        except (json.JSONDecodeError, OSError):
            return {}

    def _save(self, state: dict) -> None:
        """Save state to JSON file."""
        self._state_file.write_text(json.dumps(state, indent=2))
