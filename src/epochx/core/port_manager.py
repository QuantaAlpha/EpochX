"""SSH port allocation manager for parallel Docker containers."""

from __future__ import annotations

import json
import socket
from pathlib import Path


class PortManager:
    """Manages SSH port allocation in range 22000-22999."""

    BASE_PORT = 22000
    MAX_PORT = 22999

    def __init__(self, state_file: Path | None = None):
        if state_file is None:
            state_file = Path.home() / ".epochx" / "ports.json"
        self._state_file = state_file
        self._state_file.parent.mkdir(parents=True, exist_ok=True)

    def allocate(self, task_id: str) -> int:
        """Allocate a port for a task. Returns existing port if already allocated."""
        state = self._load()
        if task_id in state:
            return state[task_id]

        used_ports = set(state.values())
        for port in range(self.BASE_PORT, self.MAX_PORT + 1):
            if port not in used_ports and not self._port_in_use(port):
                state[task_id] = port
                self._save(state)
                return port

        raise RuntimeError(
            f"No available ports in range {self.BASE_PORT}-{self.MAX_PORT}"
        )

    def release(self, task_id: str) -> None:
        """Release all ports for a task."""
        state = self._load()
        if task_id in state:
            del state[task_id]
            self._save(state)

    def get_port(self, task_id: str) -> int | None:
        """Lookup the port allocated for a task."""
        state = self._load()
        return state.get(task_id)

    def _port_in_use(self, port: int) -> bool:
        """Check if a port is currently in use on the system."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return False
            except OSError:
                return True

    def _load(self) -> dict[str, int]:
        """Load port state from JSON file."""
        if not self._state_file.exists():
            return {}
        try:
            return json.loads(self._state_file.read_text())
        except (json.JSONDecodeError, OSError):
            return {}

    def _save(self, state: dict[str, int]) -> None:
        """Save port state to JSON file."""
        self._state_file.write_text(json.dumps(state, indent=2))
