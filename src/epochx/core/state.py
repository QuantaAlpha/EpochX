"""Run-based persistent state management.

Each run gets its own directory under ~/.epochx/runs/{run_name}/
with a run.json file containing environments and results.
A 'current' symlink points to the active run.
"""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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
    """Manages per-run state in ~/.epochx/runs/{run_name}/run.json."""

    def __init__(self, base_dir: str | Path | None = None):
        self.base_dir = Path(base_dir or os.path.expanduser("~/.epochx"))
        self.runs_dir = self.base_dir / "runs"
        self._maybe_migrate_legacy()

    # ── Run management ──────────────────────────────────────────

    def create_run(self, benchmark: str, run_name: str | None = None) -> str:
        """Create a new run directory and set it as current."""
        if not run_name:
            ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
            run_name = f"{benchmark}-{ts}"

        run_dir = self.runs_dir / run_name
        run_dir.mkdir(parents=True, exist_ok=True)

        run_data = {
            "run_name": run_name,
            "benchmark": benchmark,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "environments": {},
            "results": {},
        }
        self._save_run(run_name, run_data)
        self._set_current(run_name)
        return run_name

    def list_runs(self) -> list[dict[str, Any]]:
        """List all runs with summary info."""
        if not self.runs_dir.exists():
            return []
        current = self.current_run_name()
        runs = []
        for d in sorted(self.runs_dir.iterdir()):
            if d.is_symlink() or not d.is_dir():
                continue
            data = self._load_run(d.name)
            if data is None:
                continue
            results = data.get("results", {})
            completed = len(results)
            passed = sum(1 for r in results.values() if r.get("passed"))
            runs.append({
                "run_name": d.name,
                "benchmark": data.get("benchmark", ""),
                "completed": completed,
                "passed": passed,
                "is_current": d.name == current,
                "created_at": data.get("created_at", ""),
            })
        return runs

    def switch_run(self, run_name: str) -> None:
        """Switch the current run."""
        run_dir = self.runs_dir / run_name
        if not run_dir.exists() or run_dir.is_symlink():
            raise ValueError(f"Run '{run_name}' not found")
        self._set_current(run_name)

    def current_run_name(self) -> str | None:
        """Get the name of the current run."""
        current_link = self.runs_dir / "current"
        if not current_link.exists() and not current_link.is_symlink():
            return None
        target = current_link.resolve()
        return target.name

    def get_run_dir(self, run_name: str | None = None) -> Path:
        """Get the directory for a run (defaults to current)."""
        name = run_name or self.current_run_name()
        if not name:
            raise ValueError("No current run. Create one with 'run-create'.")
        return self.runs_dir / name

    def get_arena_dir(self, run_name: str | None = None) -> Path:
        """Get the arena workspace directory for a run."""
        return self.get_run_dir(run_name) / "arena"

    # ── Environment state ───────────────────────────────────────

    def save_environment(self, env: EnvironmentState) -> None:
        """Save or update an environment state."""
        data = self._load_current()
        data.setdefault("environments", {})[env.task_id] = asdict(env)
        self._save_current(data)

    def get_environment(self, task_id: str) -> EnvironmentState | None:
        """Get environment state by task ID."""
        data = self._load_current()
        env_data = data.get("environments", {}).get(task_id)
        if env_data is None:
            return None
        return EnvironmentState(**env_data)

    def update_status(self, task_id: str, status: str) -> None:
        """Update the status of an environment."""
        data = self._load_current()
        envs = data.get("environments", {})
        if task_id in envs:
            envs[task_id]["status"] = status
            self._save_current(data)

    def list_environments(
        self, status: str | None = None
    ) -> list[EnvironmentState]:
        """List all environments, optionally filtered by status."""
        data = self._load_current()
        envs = data.get("environments", {})
        result = []
        for env_data in envs.values():
            if status is None or env_data.get("status") == status:
                result.append(EnvironmentState(**env_data))
        return result

    def remove_environment(self, task_id: str) -> None:
        """Remove an environment state."""
        data = self._load_current()
        envs = data.get("environments", {})
        if task_id in envs:
            del envs[task_id]
            self._save_current(data)

    # ── Results ─────────────────────────────────────────────────

    def save_result(self, task_id: str, result: dict) -> None:
        """Save evaluation result for a task."""
        data = self._load_current()
        data.setdefault("results", {})[task_id] = result
        self._save_current(data)

    def get_results(self, benchmark: str | None = None) -> dict:
        """Get results, optionally filtered by benchmark."""
        data = self._load_current()
        results = data.get("results", {})
        if benchmark is None:
            return results
        return {
            k: v
            for k, v in results.items()
            if v.get("benchmark") == benchmark
        }

    # ── Internal helpers ────────────────────────────────────────

    def _load_run(self, run_name: str) -> dict | None:
        path = self.runs_dir / run_name / "run.json"
        if not path.exists():
            return None
        try:
            with open(path) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

    def _save_run(self, run_name: str, data: dict) -> None:
        path = self.runs_dir / run_name / "run.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def _load_current(self) -> dict:
        name = self.current_run_name()
        if not name:
            return {"environments": {}, "results": {}}
        data = self._load_run(name)
        if data is None:
            return {"environments": {}, "results": {}}
        return data

    def _save_current(self, data: dict) -> None:
        name = self.current_run_name()
        if not name:
            raise ValueError("No current run")
        self._save_run(name, data)

    def _set_current(self, run_name: str) -> None:
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        current_link = self.runs_dir / "current"
        if current_link.exists() or current_link.is_symlink():
            current_link.unlink()
        current_link.symlink_to(run_name)

    def _maybe_migrate_legacy(self) -> None:
        """Auto-migrate old state.json to runs/default/run.json."""
        legacy_state = self.base_dir / "state.json"
        if not legacy_state.exists():
            return

        try:
            with open(legacy_state) as f:
                old_data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return

        # Create runs/default/
        default_dir = self.runs_dir / "default"
        default_dir.mkdir(parents=True, exist_ok=True)

        # Determine benchmark from environments
        benchmark = ""
        for env in old_data.get("environments", {}).values():
            benchmark = env.get("benchmark", "")
            if benchmark:
                break

        run_data = {
            "run_name": "default",
            "benchmark": benchmark,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "environments": old_data.get("environments", {}),
            "results": old_data.get("results", {}),
        }
        self._save_run("default", run_data)

        # Move arena directory
        old_arena = self.base_dir / "arena"
        if old_arena.exists():
            new_arena = default_dir / "arena"
            if not new_arena.exists():
                shutil.move(str(old_arena), str(new_arena))

        # Set current and remove old state
        self._set_current("default")
        legacy_state.unlink()
