"""DA-Code benchmark adapter — data science agent tasks, Docker evaluation."""

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
    / "da-code"
    / "repo"
)


@register_adapter
class DACodeAdapter(BenchmarkAdapter):
    """Data science agent tasks — insight, manipulation, ML, stats, visualization."""

    name = "da-code"
    display_name = "DA-Code"
    description = (
        "Data science agent tasks — insight, manipulation, ML, stats, visualization"
    )
    resource_profile = "medium"

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
        """Load tasks from da_code/source/*.json files."""
        source_dir = self._repo_dir / "da_code" / "source"
        if not source_dir.exists():
            return []

        json_files = sorted(source_dir.glob("*.json"))
        if not json_files:
            return []

        tasks: list[Task] = []
        for json_file in json_files:
            with open(json_file, encoding="utf-8") as fh:
                data = json.load(fh)

            # Support both single-object and list-of-objects JSON files
            items = data if isinstance(data, list) else [data]

            for item in items:
                tid = str(item["id"])
                if task_ids is not None and tid not in task_ids:
                    continue

                question = item.get("question", "")
                data_files = item.get("data_files", [])
                output_file = item.get("output_file", "output.txt")
                category = item.get("category", "unknown")
                difficulty = item.get("difficulty", "unknown")

                prompt = (
                    f"You are given a data science task.\n\n"
                    f"## Question\n{question}\n\n"
                    f"## Category\n{category}\n\n"
                    f"## Data Files\n{', '.join(data_files) if data_files else 'None'}\n\n"
                    f"Write your output to the file `{output_file}`."
                )

                tasks.append(
                    Task(
                        id=f"da-code/{tid}",
                        benchmark="da-code",
                        external_id=tid,
                        prompt=prompt,
                        workspace=WorkspaceSpec(
                            type=WorkspaceType.DATA_DIR,
                            data_files=data_files,
                            data_source=str(self._repo_dir / "da_code" / "source"),
                            runtime=RuntimeType.DOCKER,
                            docker_image="da_agent-image",
                        ),
                        output_spec=OutputSpec(
                            type=OutputType.FILE_CONTENT,
                            output_file=output_file,
                        ),
                        eval_spec=EvalSpec(
                            type=EvalType.CUSTOM_SCRIPT,
                            eval_script=str(self._repo_dir / "evaluate.py"),
                            timeout=600,
                        ),
                        metadata={
                            "category": category,
                            "difficulty": difficulty,
                        },
                    )
                )

                if limit is not None and len(tasks) >= limit:
                    return tasks

        return tasks

    def prepare_image(self, task: Task) -> str | None:
        """Pull or build the DA-Code Docker image if not available."""
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
            f"Build it from the DA-Code repo: "
            f"cd {self._repo_dir} && docker build -t {image} ."
        )

    def collect_output(self, workspace_path: str, task: Task, env=None) -> str:
        """Read the output file specified in task.output_spec.output_file."""
        output_file = task.output_spec.output_file or "output.txt"
        output_path = Path(workspace_path) / output_file
        if not output_path.exists():
            return ""
        return output_path.read_text(encoding="utf-8").strip()

    def evaluate(self, task: Task, output: str) -> EvalResult:
        """Simplified: check if output was produced. Full eval is TODO (custom evaluators per category)."""
        passed = bool(output.strip())
        return EvalResult(
            task_id=task.id,
            passed=passed,
            score=1.0 if passed else 0.0,
            details={"output_length": len(output), "note": "simplified check; full eval TODO"},
        )
