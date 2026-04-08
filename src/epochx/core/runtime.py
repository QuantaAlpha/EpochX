"""Runtime layer: Host and Docker execution environments."""

from __future__ import annotations

import hashlib
import os
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from epochx.core.port_manager import PortManager
from epochx.core.task import RuntimeType, WorkspaceInfo, WorkspaceSpec


@dataclass
class ExecResult:
    """Result of a command execution."""

    returncode: int
    stdout: str
    stderr: str


class Runtime(ABC):
    """Abstract base class for runtime environments."""

    @abstractmethod
    def setup(self, task_id: str, workspace_spec: WorkspaceSpec) -> WorkspaceInfo:
        """Set up the workspace and return runtime info."""

    @abstractmethod
    def exec(self, command: str, timeout: int = 300) -> ExecResult:
        """Execute a command in the runtime environment."""

    @abstractmethod
    def teardown(self) -> None:
        """Tear down the runtime environment."""


class HostRuntime(Runtime):
    """Runtime that executes commands directly on the host."""

    def __init__(self, base_dir: Path | None = None):
        self._base_dir = base_dir or (Path.home() / ".epochx" / "arena")
        self._workspace: Path | None = None

    def setup(self, task_id: str, workspace_spec: WorkspaceSpec) -> WorkspaceInfo:
        """Create workspace directory structure."""
        self._workspace = self._base_dir / task_id
        self._workspace.mkdir(parents=True, exist_ok=True)
        (self._workspace / ".epochx").mkdir(exist_ok=True)
        return WorkspaceInfo(
            path=str(self._workspace),
            exec_prefix="bash -c",
        )

    def exec(self, command: str, timeout: int = 300) -> ExecResult:
        """Execute a shell command in the workspace directory."""
        if self._workspace is None:
            raise RuntimeError("Runtime not set up. Call setup() first.")
        try:
            result = subprocess.run(
                ["bash", "-c", command],
                cwd=str(self._workspace),
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return ExecResult(
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )
        except subprocess.TimeoutExpired:
            return ExecResult(
                returncode=-1,
                stdout="",
                stderr=f"Command timed out after {timeout}s",
            )

    def teardown(self) -> None:
        """No-op for host runtime (keep workspace for inspection)."""
        pass


class DockerRuntime(Runtime):
    """Runtime that executes commands in a Docker container via SSH."""

    def __init__(
        self,
        base_dir: Path | None = None,
        port_manager: PortManager | None = None,
        docker_image: str = "python:3.11-slim",
    ):
        self._base_dir = base_dir or (Path.home() / ".epochx" / "arena")
        self._port_manager = port_manager or PortManager()
        self._docker_image = docker_image
        self._workspace: Path | None = None
        self._container_id: str | None = None
        self._ssh_port: int | None = None
        self._task_id: str | None = None
        self._ssh_host: str | None = None

    def setup(self, task_id: str, workspace_spec: WorkspaceSpec) -> WorkspaceInfo:
        """Create workspace, start Docker container with SSH access."""
        import docker as docker_lib

        self._task_id = task_id
        self._workspace = self._base_dir / task_id
        self._workspace.mkdir(parents=True, exist_ok=True)
        (self._workspace / ".epochx").mkdir(exist_ok=True)

        # Allocate SSH port
        self._ssh_port = self._port_manager.allocate(task_id)
        # Short container name: benchmark prefix (3 chars) + 8-char hash
        prefix = task_id.split("/")[0][:3] if "/" in task_id else task_id[:3]
        short_hash = hashlib.sha256(task_id.encode()).hexdigest()[:8]
        container_safe_id = f"{prefix}-{short_hash}"
        self._ssh_host = f"epochx-{container_safe_id}"

        # Determine docker image — raise clear error if not found
        image = workspace_spec.docker_image or self._docker_image
        client = docker_lib.from_env()

        try:
            client.images.get(image)
        except docker_lib.errors.ImageNotFound:
            raise RuntimeError(
                f"Docker image '{image}' not found locally. "
                f"The benchmark adapter should have prepared it via prepare_image(). "
                f"Try: docker pull {image}"
            )

        # Start container
        # Mount .epochx/ for metadata exchange at a non-conflicting path.
        # Pre-built images (e.g. SWE-bench Pro) have their own repo inside.
        epochx_dir = self._workspace / ".epochx"
        epochx_dir.mkdir(parents=True, exist_ok=True)
        volumes = {str(epochx_dir): {"bind": "/.epochx", "mode": "rw"}}

        container = client.containers.run(
            image,
            entrypoint="/bin/bash",
            command=["-c", "sleep infinity"],
            detach=True,
            volumes=volumes,
            ports={"22/tcp": self._ssh_port},
            name=f"epochx-{container_safe_id}",
            remove=True,
        )
        self._container_id = container.id

        # Ensure we have an SSH key pair for epochx
        self._ensure_ssh_key()
        pubkey = self._get_ssh_pubkey()

        # Single exec_run: install sshd (only if missing), configure, inject key, start
        setup_script = f"""
set -e
# Install sshd only if not already present
if ! command -v sshd >/dev/null 2>&1; then
    (apt-get update -qq && apt-get install -y -qq openssh-server 2>/dev/null) || \
    (apk add --no-cache openssh 2>/dev/null) || \
    echo 'sshd install skipped'
fi
mkdir -p /run/sshd
ssh-keygen -A 2>/dev/null || true
cat >> /etc/ssh/sshd_config << 'SSHEOF'
PermitRootLogin yes
PermitRootLogin without-password
PubkeyAuthentication yes
SSHEOF
mkdir -p /root/.ssh && chmod 700 /root/.ssh
echo "{pubkey}" >> /root/.ssh/authorized_keys
chmod 600 /root/.ssh/authorized_keys
/usr/sbin/sshd 2>/dev/null || true

# ── Trajectory: auto-log ALL bash commands (interactive + non-interactive) ──
# Uses DEBUG trap which fires for every command in every bash session,
# including non-interactive 'ssh host "cmd"' invocations by agents.
cat > /etc/bash.epochx_log << 'LOGEOF'
_epochx_trap() {{
    local cmd="$BASH_COMMAND"
    case "$cmd" in _epochx_trap*|true|false|"") return;; esac
    [ -d "/.epochx" ] && printf '{{"ts":"%s","cmd":"%s"}}\\n' \
        "$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || echo unknown)" \
        "$(echo "$cmd" | head -c 2000 | sed 's/\\\\/\\\\\\\\/g; s/"/\\\\"/g' | tr '\\n' ' ')" \
        >> /.epochx/ssh_log.jsonl 2>/dev/null
}}
trap '_epochx_trap' DEBUG
LOGEOF
# Inject into ALL bash startup paths so non-interactive SSH also picks it up
for f in /etc/bash.bashrc /root/.bashrc; do
    grep -q 'epochx_log' "$f" 2>/dev/null || echo '. /etc/bash.epochx_log' >> "$f" 2>/dev/null
done
# Set BASH_ENV in sshd so non-interactive 'ssh host "cmd"' also sources it
# This is the critical line — without it, non-interactive SSH won't log commands.
echo 'SetEnv BASH_ENV=/etc/bash.epochx_log' >> /etc/ssh/sshd_config 2>/dev/null || true
# Restart sshd to pick up the new config
pkill sshd 2>/dev/null; /usr/sbin/sshd 2>/dev/null || true
"""
        container.exec_run(["bash", "-c", setup_script])

        # Write SSH config entry (with key path)
        self._write_ssh_config()

        # Detect working directory inside container (git repo root)
        container_workdir = self._detect_workdir(container)

        return WorkspaceInfo(
            path=str(self._workspace),
            ssh_host=self._ssh_host,
            ssh_port=self._ssh_port,
            container_id=self._container_id,
            exec_prefix=f"ssh {self._ssh_host}",
            container_workdir=container_workdir,
        )

    def exec(self, command: str, timeout: int = 300) -> ExecResult:
        """Execute command via SSH in the Docker container."""
        if self._ssh_host is None:
            raise RuntimeError("Runtime not set up. Call setup() first.")
        try:
            result = subprocess.run(
                [
                    "ssh",
                    "-o", "StrictHostKeyChecking=no",
                    "-o", "UserKnownHostsFile=/dev/null",
                    self._ssh_host,
                    command,
                ],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return ExecResult(
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )
        except subprocess.TimeoutExpired:
            return ExecResult(
                returncode=-1,
                stdout="",
                stderr=f"Command timed out after {timeout}s",
            )

    def teardown(self) -> None:
        """Stop container, release port, remove SSH config."""
        if self._container_id:
            try:
                import docker as docker_lib

                client = docker_lib.from_env()
                container = client.containers.get(self._container_id)
                container.stop(timeout=5)
            except Exception:
                pass
            self._container_id = None

        if self._task_id:
            self._port_manager.release(self._task_id)

        if self._ssh_host:
            self._remove_ssh_config()

    @staticmethod
    def _detect_workdir(container) -> str:
        """Detect the git repo working directory inside the container.

        Checks common locations: /testbed, /app, /workspace, /repo.
        Falls back to /testbed if no git repo found.
        """
        candidates = ["/testbed", "/app", "/workspace", "/repo"]
        for path in candidates:
            exit_code, output = container.exec_run(
                ["bash", "-c", f"test -d {path}/.git && echo yes || echo no"]
            )
            if output.decode().strip() == "yes":
                return path
        # Fallback: check WORKDIR from image
        exit_code, output = container.exec_run(["bash", "-c", "pwd"])
        workdir = output.decode().strip()
        if workdir and workdir != "/":
            return workdir
        return "/testbed"

    @staticmethod
    def _ensure_ssh_key() -> None:
        """Generate an epochx-specific SSH key pair if it doesn't exist."""
        key_path = Path.home() / ".ssh" / "epochx_key"
        if key_path.exists():
            return
        key_path.parent.mkdir(mode=0o700, exist_ok=True)
        subprocess.run(
            ["ssh-keygen", "-t", "ed25519", "-f", str(key_path),
             "-N", "", "-q", "-C", "epochx-auto"],
            check=True,
        )

    @staticmethod
    def _get_ssh_pubkey() -> str:
        """Read the epochx SSH public key."""
        pubkey_path = Path.home() / ".ssh" / "epochx_key.pub"
        return pubkey_path.read_text().strip()

    def _write_ssh_config(self) -> None:
        """Write SSH config entry for the container."""
        ssh_dir = Path.home() / ".ssh"
        ssh_dir.mkdir(mode=0o700, exist_ok=True)
        config_file = ssh_dir / "config"
        key_path = ssh_dir / "epochx_key"

        entry = (
            f"\n# epochx-managed: {self._ssh_host}\n"
            f"Host {self._ssh_host}\n"
            f"    HostName 127.0.0.1\n"
            f"    Port {self._ssh_port}\n"
            f"    User root\n"
            f"    IdentityFile {key_path}\n"
            f"    StrictHostKeyChecking no\n"
            f"    UserKnownHostsFile /dev/null\n"
            f"    LogLevel ERROR\n"
        )

        existing = config_file.read_text() if config_file.exists() else ""
        # Avoid duplicate entries
        if f"# epochx-managed: {self._ssh_host}" not in existing:
            with config_file.open("a") as f:
                f.write(entry)

    def _remove_ssh_config(self) -> None:
        """Remove SSH config entry for the container."""
        config_file = Path.home() / ".ssh" / "config"
        if not config_file.exists():
            return

        lines = config_file.read_text().splitlines(keepends=True)
        new_lines = []
        skip = False
        for line in lines:
            if f"# epochx-managed: {self._ssh_host}" in line:
                skip = True
                continue
            if skip:
                if line.startswith("Host ") or (line.strip() == "" and not line.startswith("    ")):
                    skip = False
                    if line.strip():
                        new_lines.append(line)
                continue
            new_lines.append(line)
        config_file.write_text("".join(new_lines))


class RuntimeFactory:
    """Factory for creating runtime instances."""

    @staticmethod
    def create(
        runtime_type: RuntimeType,
        base_dir: Path | None = None,
        port_manager: PortManager | None = None,
        docker_image: str = "python:3.11-slim",
    ) -> Runtime:
        """Create a runtime instance based on type."""
        if runtime_type == RuntimeType.HOST or runtime_type == RuntimeType.UV:
            return HostRuntime(base_dir=base_dir)
        elif runtime_type == RuntimeType.DOCKER:
            return DockerRuntime(
                base_dir=base_dir,
                port_manager=port_manager,
                docker_image=docker_image,
            )
        else:
            raise ValueError(f"Unsupported runtime type: {runtime_type}")
