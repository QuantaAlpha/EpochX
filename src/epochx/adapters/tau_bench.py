"""tau-bench adapter — multi-turn dialogue agent eval across domains."""

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
    / "tau-bench"
    / "repo"
)

_OUTPUT_FILE = ".epochx/trajectory.json"


@register_adapter
class TauBenchAdapter(BenchmarkAdapter):
    """Multi-turn dialogue agent eval — airline/retail/telecom/banking domains."""

    name = "tau-bench"
    display_name = "tau-bench"
    description = (
        "Multi-turn dialogue agent eval — airline/retail/telecom/banking domains"
    )
    resource_profile = "light"

    def __init__(self, repo_dir: Path | str | None = None) -> None:
        self._repo_dir = Path(repo_dir) if repo_dir else _DEFAULT_REPO_DIR

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
        """Load tasks from data/tau2/domains/<domain>/tasks.json files."""
        domains_dir = self._repo_dir / "data" / "tau2" / "domains"
        if not domains_dir.exists():
            return []

        tasks: list[Task] = []
        for domain_dir in sorted(domains_dir.iterdir()):
            if not domain_dir.is_dir():
                continue
            tasks_file = domain_dir / "tasks.json"
            if not tasks_file.exists():
                continue

            domain = domain_dir.name
            with open(tasks_file, encoding="utf-8") as fh:
                task_list = json.load(fh)

            for idx, task_data in enumerate(task_list):
                tid = f"{domain}-{idx}"
                if task_ids is not None and tid not in task_ids:
                    continue

                # Build a prompt from the user scenario
                scenario = task_data.get("user_scenario", {})
                instructions = scenario.get("instructions", {})

                # instructions can be a dict (airline/retail/telecom) or a string (banking/mock)
                if isinstance(instructions, str):
                    reason = ""
                    task_instructions = instructions
                    known_info = ""
                    unknown_info = ""
                else:
                    reason = instructions.get("reason_for_call", "")
                    task_instructions = instructions.get("task_instructions", "")
                    known_info = instructions.get("known_info", "")
                    unknown_info = instructions.get("unknown_info", "")

                prompt = (
                    f"You are a dialogue agent for the '{domain}' domain.\n\n"
                    f"## Task\n{reason}\n\n"
                    f"## Instructions\n{task_instructions}\n\n"
                    f"## Known info\n{known_info}\n\n"
                    f"## Unknown info\n{unknown_info}\n\n"
                    f"Write your full dialogue trajectory as JSON "
                    f"to the file `{_OUTPUT_FILE}`."
                )

                tasks.append(
                    Task(
                        id=f"tau-bench/{tid}",
                        benchmark="tau-bench",
                        external_id=tid,
                        prompt=prompt,
                        workspace=WorkspaceSpec(
                            type=WorkspaceType.API_ONLY,
                            runtime=RuntimeType.HOST,
                        ),
                        output_spec=OutputSpec(
                            type=OutputType.TRAJECTORY,
                            output_file=_OUTPUT_FILE,
                        ),
                        eval_spec=EvalSpec(
                            type=EvalType.REWARD_FUNCTION,
                            eval_script=str(self._repo_dir / "src" / "tau2"),
                            timeout=600,
                        ),
                        metadata={
                            "domain": domain,
                            "task_index": idx,
                        },
                    )
                )

                if limit is not None and len(tasks) >= limit:
                    return tasks

        return tasks

    def collect_output(self, workspace_path: str, task: Task, env=None) -> str:
        """Read the agent's trajectory from <workspace>/.epochx/trajectory.json."""
        traj_path = Path(workspace_path) / _OUTPUT_FILE
        if not traj_path.exists():
            return ""
        return traj_path.read_text(encoding="utf-8").strip()

    def evaluate(self, task: Task, output: str) -> EvalResult:
        """Basic evaluation: check if a valid trajectory was produced.

        Full evaluation requires the tau2 framework (reward function);
        this method performs a lightweight sanity check only.
        """
        if not output:
            return EvalResult(
                task_id=task.id,
                passed=False,
                score=0.0,
                details={"reason": "no trajectory produced"},
            )

        try:
            parsed = json.loads(output)
        except json.JSONDecodeError as exc:
            return EvalResult(
                task_id=task.id,
                passed=False,
                score=0.0,
                details={"reason": f"invalid JSON: {exc}"},
            )

        # TODO: integrate tau2 reward function for full scoring
        return EvalResult(
            task_id=task.id,
            passed=True,
            score=1.0,
            details={"reason": "trajectory produced (basic check only)", "keys": list(parsed.keys()) if isinstance(parsed, dict) else f"list[{len(parsed)}]"},
        )
