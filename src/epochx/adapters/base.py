"""BenchmarkAdapter base class and registry."""

from __future__ import annotations

from abc import ABC, abstractmethod

from epochx.core.task import EvalResult, RuntimeType, Task


class BenchmarkAdapter(ABC):
    """Base class for all benchmark adapters.

    Each adapter knows how to fetch tasks from a specific benchmark,
    collect agent output, and evaluate results.

    ## Adapter Development Rules

    ### evaluate() MUST reuse original benchmark toolchain

    Each benchmark ships its own evaluation scripts or pip-installable CLI.
    The ``evaluate()`` method should call those tools via ``subprocess.run()``,
    NOT reimplement the evaluation logic in Python.

    Priority order:
    1. **pip-installed CLI** — if the benchmark provides a pip package with
       an eval command (e.g. ``python -m swebench.harness.run_evaluation``,
       ``fb eval``, ``appworld evaluate``), call it directly.
    2. **Copy eval scripts into container** — if no pip package exists,
       copy the benchmark repo's eval scripts to the workspace and invoke
       them via subprocess.

    Never import benchmark internals or rewrite scoring logic.

    ### collect_output() for Docker tasks must use SSH

    When ``env.ssh_host`` is available, collect output from the running
    container via SSH (e.g. ``ssh <host> 'cd /app && git diff'``),
    not from the host workspace directory.
    """

    name: str  # e.g. "dabstep"
    display_name: str  # e.g. "DABstep"
    description: str
    resource_profile: str = "light"  # "light" | "medium" | "heavy"

    @property
    def agent_runtime(self) -> RuntimeType:
        return RuntimeType.HOST

    @property
    def eval_runtime(self) -> RuntimeType:
        return RuntimeType.HOST

    @abstractmethod
    def fetch_tasks(
        self,
        limit: int | None = None,
        task_ids: list[str] | None = None,
    ) -> list[Task]:
        """Return a list of Task objects from this benchmark."""

    @abstractmethod
    def collect_output(self, workspace_path: str, task: Task, env=None) -> str:
        """Read the agent's answer from the workspace.

        Args:
            workspace_path: Host-side workspace directory.
            task: The Task being collected.
            env: Optional EnvironmentState with SSH/container info for Docker tasks.
        """

    @abstractmethod
    def evaluate(self, task: Task, output: str) -> EvalResult:
        """Score a single task given the agent output string."""

    def prepare_image(self, task: Task) -> str | None:
        """Ensure the Docker image for this task is available.

        Called by Runner before starting the container. Should:
        1. Check if image exists locally
        2. If not, try to pull from registry
        3. If can't pull, build locally
        4. Return the final image name, or None if no Docker needed.

        Raises RuntimeError if image cannot be prepared.
        """
        return None  # Default: no image preparation needed

    def get_docker_image(self, task: Task) -> str | None:
        """Return a Docker image name if the task needs one."""
        return None

    def post_setup(self, workspace_path: str, task: Task) -> None:
        """Hook called after workspace is created, before the agent starts."""

    def info(self) -> dict:
        """Return a summary dict suitable for CLI / API listing."""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "agent_runtime": self.agent_runtime.value,
            "eval_runtime": self.eval_runtime.value,
            "resource_profile": self.resource_profile,
        }


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_REGISTRY: dict[str, type[BenchmarkAdapter]] = {}


def register_adapter(cls: type[BenchmarkAdapter]) -> type[BenchmarkAdapter]:
    """Class decorator that registers a BenchmarkAdapter subclass."""
    _REGISTRY[cls.name] = cls
    return cls


def get_adapter(name: str, **kwargs) -> BenchmarkAdapter:
    """Instantiate a registered adapter by name."""
    if name not in _REGISTRY:
        available = ", ".join(sorted(_REGISTRY)) or "(none)"
        raise KeyError(f"Unknown adapter {name!r}. Available: {available}")
    return _REGISTRY[name](**kwargs)


def list_adapters() -> list[dict]:
    """Return info dicts for every registered adapter."""
    return [cls().info() for cls in _REGISTRY.values()]
