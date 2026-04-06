"""DABstep benchmark adapter — financial data analysis, exact-match scoring."""

from __future__ import annotations

import json
import shutil
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

_DEFAULT_DATA_DIR = (
    Path(__file__).resolve().parents[3]  # src/epochx/adapters -> repo root
    / "benchmarks"
    / "dabstep"
    / "repo"
    / "data"
)

_OUTPUT_FILE = ".epochx/answer.txt"


@register_adapter
class DABstepAdapter(BenchmarkAdapter):
    """Financial data analysis benchmark — 450 tasks (easy + hard), exact-match scoring."""

    name = "dabstep"
    display_name = "DABstep"
    description = (
        "Financial data analysis benchmark — 450 tasks (easy + hard), exact-match scoring"
    )
    resource_profile = "light"

    def __init__(self, data_dir: Path | str | None = None) -> None:
        self._data_dir = Path(data_dir) if data_dir else _DEFAULT_DATA_DIR

    # ------------------------------------------------------------------
    # Runtime properties
    # ------------------------------------------------------------------

    @property
    def agent_runtime(self) -> RuntimeType:
        return RuntimeType.HOST

    @property
    def eval_runtime(self) -> RuntimeType:
        return RuntimeType.HOST

    # ------------------------------------------------------------------
    # Core interface
    # ------------------------------------------------------------------

    def fetch_tasks(
        self,
        limit: int | None = None,
        task_ids: list[str] | None = None,
    ) -> list[Task]:
        """Load tasks from dev.jsonl (has answers) falling back to all.jsonl."""
        tasks_dir = self._data_dir / "tasks"
        dev_path = tasks_dir / "dev.jsonl"
        all_path = tasks_dir / "all.jsonl"

        path = dev_path if dev_path.exists() else all_path
        if not path.exists():
            raise FileNotFoundError(
                f"No task file found. Looked for {dev_path} and {all_path}"
            )

        rows: list[dict] = []
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                if task_ids is not None and str(row["task_id"]) not in task_ids:
                    continue
                rows.append(row)
                if limit is not None and len(rows) >= limit:
                    break

        context_files = self._list_context_files()

        tasks: list[Task] = []
        for row in rows:
            tid = str(row["task_id"])
            question = row["question"]
            guidelines = row.get("guidelines", "")
            level = row.get("level", "unknown")
            answer = row.get("answer", "")

            prompt = (
                f"You are given a financial data analysis question.\n\n"
                f"## Question\n{question}\n\n"
                f"## Guidelines\n{guidelines}\n\n"
                f"The data directory contains these files: {', '.join(context_files)}.\n\n"
                f"Write your final answer (and nothing else) to the file `{_OUTPUT_FILE}`."
            )

            tasks.append(
                Task(
                    id=f"dabstep/{tid}",
                    benchmark="dabstep",
                    external_id=tid,
                    prompt=prompt,
                    workspace=WorkspaceSpec(
                        type=WorkspaceType.DATA_DIR,
                        data_files=context_files,
                        data_source=str(self._data_dir / "context"),
                        runtime=RuntimeType.HOST,
                    ),
                    output_spec=OutputSpec(
                        type=OutputType.ANSWER_STRING,
                        output_file=_OUTPUT_FILE,
                    ),
                    eval_spec=EvalSpec(
                        type=EvalType.EXACT_MATCH,
                        expected_answer=answer if answer else None,
                    ),
                    metadata={
                        "level": level,
                        "guidelines": guidelines,
                    },
                )
            )

        return tasks

    def collect_output(self, workspace_path: str, task: Task, env=None) -> str:
        """Read the agent's answer from <workspace>/.epochx/answer.txt."""
        answer_path = Path(workspace_path) / _OUTPUT_FILE
        if not answer_path.exists():
            return ""
        return answer_path.read_text(encoding="utf-8").strip()

    def evaluate(self, task: Task, output: str) -> EvalResult:
        """Exact string match after stripping whitespace."""
        expected = (task.eval_spec.expected_answer or "").strip()
        actual = output.strip()
        passed = actual == expected
        return EvalResult(
            task_id=task.id,
            passed=passed,
            score=1.0 if passed else 0.0,
            details={"expected": expected, "actual": actual},
        )

    def post_setup(self, workspace_path: str, task: Task) -> None:
        """Copy context files into workspace/data/."""
        context_src = self._data_dir / "context"
        if not context_src.exists():
            return
        dest = Path(workspace_path) / "data"
        dest.mkdir(parents=True, exist_ok=True)
        for item in context_src.iterdir():
            target = dest / item.name
            if item.is_file():
                shutil.copy2(item, target)
            elif item.is_dir():
                shutil.copytree(item, target, dirs_exist_ok=True)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _list_context_files(self) -> list[str]:
        context_dir = self._data_dir / "context"
        if not context_dir.exists():
            return []
        return sorted(f.name for f in context_dir.iterdir() if f.is_file())
