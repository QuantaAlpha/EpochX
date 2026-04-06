"""CORE-Bench benchmark adapter — computational reproducibility tasks, Docker-in-Docker."""

from __future__ import annotations

import json
from pathlib import Path

from epochx.adapters.base import BenchmarkAdapter, register_adapter
from epochx.core.task import (
    EvalResult,
    EvalSpec,
    EvalType,
    OutputSpec,
    OutputType,
    RuntimeType,
    Task,
    WorkspaceSpec,
    WorkspaceType,
)

_DEFAULT_REPO_DIR = (
    Path(__file__).resolve().parents[3]  # src/epochx/adapters -> repo root
    / "benchmarks"
    / "core-bench"
    / "repo"
)


@register_adapter
class COREBenchAdapter(BenchmarkAdapter):
    """90 computational reproducibility tasks — Docker-in-Docker, vision+text grading."""

    name = "core-bench"
    display_name = "CORE-Bench"
    description = (
        "90 computational reproducibility tasks — Docker-in-Docker, vision+text grading"
    )
    resource_profile = "heavy"

    def __init__(self, repo_dir: Path | str | None = None) -> None:
        self._repo_dir = Path(repo_dir) if repo_dir else _DEFAULT_REPO_DIR

    # ------------------------------------------------------------------
    # Runtime properties
    # ------------------------------------------------------------------

    @property
    def agent_runtime(self) -> RuntimeType:
        return RuntimeType.DOCKER

    @property
    def eval_runtime(self) -> RuntimeType:
        return RuntimeType.DOCKER

    # ------------------------------------------------------------------
    # Core interface
    # ------------------------------------------------------------------

    def fetch_tasks(
        self,
        limit: int | None = None,
        task_ids: list[str] | None = None,
    ) -> list[Task]:
        """Load tasks from benchmark/dataset/ directories."""
        dataset_dir = self._repo_dir / "benchmark" / "dataset"
        if not dataset_dir.exists():
            return []

        tasks: list[Task] = []
        for task_dir in sorted(dataset_dir.iterdir()):
            if not task_dir.is_dir():
                continue

            tid = task_dir.name
            if task_ids is not None and tid not in task_ids:
                continue

            # Load optional metadata
            metadata: dict = {}
            metadata_path = task_dir / "metadata.json"
            if metadata_path.exists():
                with open(metadata_path, encoding="utf-8") as fh:
                    metadata = json.load(fh)

            # Load optional README for prompt
            readme_path = task_dir / "README.md"
            description = ""
            if readme_path.exists():
                description = readme_path.read_text(encoding="utf-8").strip()

            prompt = (
                f"You are given a computational reproducibility task.\n\n"
                f"## Task ID\n{tid}\n\n"
            )
            if description:
                prompt += f"## Description\n{description}\n\n"
            prompt += (
                f"Reproduce the computational results described in the task.\n"
                f"Write your results to the `results/` directory."
            )

            tasks.append(
                Task(
                    id=f"core-bench/{tid}",
                    benchmark="core-bench",
                    external_id=tid,
                    prompt=prompt,
                    workspace=WorkspaceSpec(
                        type=WorkspaceType.DATA_DIR,
                        data_files=[f.name for f in task_dir.iterdir() if f.is_file()],
                        data_source=str(task_dir),
                        runtime=RuntimeType.DOCKER,
                        docker_image="core-bench:latest",
                        system_deps=["docker"],
                    ),
                    output_spec=OutputSpec(
                        type=OutputType.FILE_CONTENT,
                        output_file="results/",
                    ),
                    eval_spec=EvalSpec(
                        type=EvalType.CUSTOM_SCRIPT,
                        eval_script=str(self._repo_dir / "main.py"),
                        timeout=3600,
                    ),
                    metadata=metadata,
                )
            )

            if limit is not None and len(tasks) >= limit:
                return tasks

        return tasks

    def prepare_image(self, task: Task) -> str | None:
        """Pull or build the CORE-Bench Docker image if not available."""
        image = task.workspace.docker_image
        if not image:
            return None

        try:
            import docker as docker_lib
            client = docker_lib.from_env()
            client.images.get(image)
            return image
        except Exception:
            pass

        # Try to pull
        try:
            import docker as docker_lib
            client = docker_lib.from_env()
            client.images.pull(image)
            return image
        except Exception:
            pass

        # Provide build instructions
        raise RuntimeError(
            f"Docker image '{image}' not found and cannot be pulled. "
            f"Build it from the CORE-Bench repo: "
            f"cd {self._repo_dir} && docker build -t {image} ."
        )

    def collect_output(self, workspace_path: str, task: Task, env=None) -> str:
        """Collect all files from results/ directory, concatenated with separators."""
        results_dir = Path(workspace_path) / "results"
        if not results_dir.exists():
            return ""

        parts: list[str] = []
        for f in sorted(results_dir.rglob("*")):
            if not f.is_file():
                continue
            try:
                content = f.read_text(encoding="utf-8").strip()
            except (UnicodeDecodeError, OSError):
                content = f"<binary file: {f.name}>"
            rel = f.relative_to(results_dir)
            parts.append(f"--- {rel} ---\n{content}")

        return "\n\n".join(parts)

    def evaluate(self, task: Task, output: str) -> EvalResult:
        """Simplified: check if results were produced. Full eval requires vision+text grading (TODO)."""
        passed = bool(output.strip())
        return EvalResult(
            task_id=task.id,
            passed=passed,
            score=1.0 if passed else 0.0,
            details={"output_length": len(output), "note": "simplified check; full eval TODO"},
        )
