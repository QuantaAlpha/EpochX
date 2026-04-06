"""Terminal-Bench 2.0 adapter — 89+ hard terminal tasks, Docker-based verification.

Tasks are self-contained with pre-built Docker images, instruction files,
and test scripts that verify the final container state.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
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
    / "terminal-bench"
    / "repo"
)

_OUTPUT_FILE = ".epochx/answer.txt"


def _parse_toml(path: Path) -> dict:
    """Parse a TOML file, using tomllib (3.11+) or tomli as fallback."""
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib
        except ImportError:
            raise ImportError(
                "Python 3.11+ or the 'tomli' package is required for TOML parsing. "
                "Install: uv pip install tomli"
            )
    with open(path, "rb") as f:
        return tomllib.load(f)


@register_adapter
class TerminalBenchAdapter(BenchmarkAdapter):
    """89+ hard terminal tasks — coding, sysadmin, scientific computing, Docker-verified."""

    name = "terminal-bench"
    display_name = "Terminal-Bench 2.0"
    description = (
        "89+ hard terminal tasks — coding, sysadmin, scientific computing, "
        "Docker-verified"
    )
    resource_profile = "medium"

    def __init__(self, repo_dir: Path | str | None = None) -> None:
        self._repo_dir = Path(repo_dir) if repo_dir else _DEFAULT_REPO_DIR

    @property
    def agent_runtime(self) -> RuntimeType:
        return RuntimeType.DOCKER

    @property
    def eval_runtime(self) -> RuntimeType:
        return RuntimeType.DOCKER

    def fetch_tasks(
        self,
        limit: int | None = None,
        task_ids: list[str] | None = None,
    ) -> list[Task]:
        """Scan repo for task directories containing task.toml + instruction.md."""
        if not self._repo_dir.exists():
            return []

        tasks: list[Task] = []
        for task_dir in sorted(self._repo_dir.iterdir()):
            if not task_dir.is_dir():
                continue
            toml_path = task_dir / "task.toml"
            instruction_path = task_dir / "instruction.md"
            if not toml_path.exists() or not instruction_path.exists():
                continue

            tid = task_dir.name
            if task_ids is not None and tid not in task_ids:
                continue

            meta = _parse_toml(toml_path)
            instruction = instruction_path.read_text(encoding="utf-8").strip()

            env_cfg = meta.get("environment", {})
            task_meta = meta.get("metadata", {})
            verifier_cfg = meta.get("verifier", {})
            agent_cfg = meta.get("agent", {})

            docker_image = env_cfg.get("docker_image", "")
            difficulty = task_meta.get("difficulty", "unknown")
            category = task_meta.get("category", "")
            tags = task_meta.get("tags", [])
            agent_timeout = int(agent_cfg.get("timeout_sec", 900))
            verifier_timeout = int(verifier_cfg.get("timeout_sec", 900))

            prompt = (
                f"You are working in a terminal environment inside a Docker container.\n\n"
                f"## Task: {tid}\n\n"
                f"**Difficulty:** {difficulty}\n"
                f"**Category:** {category}\n\n"
                f"## Instructions\n\n{instruction}\n\n"
                f"Complete the task by working directly in the container. "
                f"Your work will be verified by automated tests that check "
                f"the final state of the container."
            )

            tasks.append(
                Task(
                    id=f"terminal-bench/{tid}",
                    benchmark="terminal-bench",
                    external_id=tid,
                    prompt=prompt,
                    workspace=WorkspaceSpec(
                        type=WorkspaceType.DATA_DIR,
                        runtime=RuntimeType.DOCKER,
                        docker_image=docker_image,
                    ),
                    output_spec=OutputSpec(
                        type=OutputType.SNAPSHOT_DIFF,
                    ),
                    eval_spec=EvalSpec(
                        type=EvalType.CUSTOM_SCRIPT,
                        eval_script=str(task_dir / "tests"),
                        timeout=verifier_timeout,
                    ),
                    metadata={
                        "difficulty": difficulty,
                        "category": category,
                        "tags": tags,
                        "docker_image": docker_image,
                        "agent_timeout_sec": agent_timeout,
                        "verifier_timeout_sec": verifier_timeout,
                        "task_dir": str(task_dir),
                        "cpus": env_cfg.get("cpus", 1),
                        "memory": env_cfg.get("memory", "2G"),
                    },
                )
            )

            if limit is not None and len(tasks) >= limit:
                return tasks

        return tasks

    def prepare_image(self, task: Task) -> str | None:
        """Pull pre-built Docker image from DockerHub."""
        image = task.workspace.docker_image
        if not image:
            return None

        import docker as docker_lib

        client = docker_lib.from_env()

        try:
            client.images.get(image)
            return image
        except docker_lib.errors.ImageNotFound:
            pass

        repo_tag = image.split(":", 1)
        repo = repo_tag[0]
        tag = repo_tag[1] if len(repo_tag) > 1 else "latest"

        try:
            print(f"Pulling {image} ...", file=sys.stderr)
            client.images.pull(repo, tag=tag)
            return image
        except docker_lib.errors.APIError as e:
            raise RuntimeError(
                f"Failed to pull '{image}': {e}\n"
                f"Manual: docker pull {image}"
            )

    def post_setup(self, workspace_path: str, task: Task) -> None:
        """Copy test files into workspace/.epochx/tests/ for later verification."""
        task_dir = Path(task.metadata.get("task_dir", ""))
        tests_src = task_dir / "tests"
        if not tests_src.exists():
            return
        dest = Path(workspace_path) / ".epochx" / "tests"
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copytree(tests_src, dest, dirs_exist_ok=True)

    def collect_output(self, workspace_path: str, task: Task, env=None) -> str:
        """Run verification tests inside the container and capture results.

        The test.sh script writes reward (0 or 1) to /logs/verifier/reward.txt.
        We run it via SSH while the container is still alive.
        """
        if not (env and env.ssh_host):
            return json.dumps({"reward": 0, "reason": "No SSH access to container"})

        ssh_host = env.ssh_host
        verifier_timeout = task.metadata.get("verifier_timeout_sec", 900)

        try:
            # 1. Copy test files from /.epochx/tests/ to /tests/ inside container
            setup_cmd = (
                "mkdir -p /tests /logs/verifier && "
                "cp -r /.epochx/tests/* /tests/ && "
                "chmod +x /tests/test.sh"
            )
            subprocess.run(
                ["ssh", ssh_host, setup_cmd],
                capture_output=True, text=True, timeout=30,
            )

            # 2. Run test.sh inside the container
            test_cmd = "cd /tests && bash test.sh 2>&1"
            result = subprocess.run(
                ["ssh", ssh_host, test_cmd],
                capture_output=True, text=True,
                timeout=verifier_timeout + 60,
            )
            test_output = result.stdout + result.stderr

            # 3. Read reward.txt
            reward_cmd = "cat /logs/verifier/reward.txt 2>/dev/null || echo -1"
            reward_result = subprocess.run(
                ["ssh", ssh_host, reward_cmd],
                capture_output=True, text=True, timeout=10,
            )
            reward_str = reward_result.stdout.strip()
            try:
                reward = int(reward_str)
            except ValueError:
                reward = 0

            # 4. Try to read CTRF report for detailed test info
            ctrf_cmd = "cat /logs/verifier/ctrf.json 2>/dev/null || echo {}"
            ctrf_result = subprocess.run(
                ["ssh", ssh_host, ctrf_cmd],
                capture_output=True, text=True, timeout=10,
            )
            ctrf_data = ctrf_result.stdout.strip()

            collect_result = {
                "reward": reward,
                "test_output_tail": test_output[-2000:] if test_output else "",
                "ctrf": ctrf_data,
            }
            return json.dumps(collect_result)

        except subprocess.TimeoutExpired:
            return json.dumps({
                "reward": 0,
                "reason": f"Verification timed out after {verifier_timeout}s",
            })
        except Exception as e:
            return json.dumps({
                "reward": 0,
                "reason": f"Verification error: {e}",
            })

    def evaluate(self, task: Task, output: str) -> EvalResult:
        """Parse the collected verification results."""
        if not output:
            return EvalResult(
                task_id=task.id, passed=False, score=0.0,
                details={"reason": "No output collected"},
            )

        try:
            data = json.loads(output)
        except json.JSONDecodeError:
            return EvalResult(
                task_id=task.id, passed=False, score=0.0,
                details={"reason": f"Invalid JSON output: {output[:200]}"},
            )

        reward = data.get("reward", 0)
        passed = reward == 1

        details: dict = {
            "reward": reward,
        }

        # Parse CTRF report for test details
        ctrf_raw = data.get("ctrf", "{}")
        try:
            ctrf = json.loads(ctrf_raw) if isinstance(ctrf_raw, str) else ctrf_raw
            if ctrf and isinstance(ctrf, dict):
                summary = ctrf.get("results", {}).get("summary", {})
                if summary:
                    details["tests_total"] = summary.get("tests", 0)
                    details["tests_passed"] = summary.get("passed", 0)
                    details["tests_failed"] = summary.get("failed", 0)
        except (json.JSONDecodeError, AttributeError):
            pass

        if "reason" in data:
            details["reason"] = data["reason"]

        # Include tail of test output for debugging
        test_tail = data.get("test_output_tail", "")
        if test_tail and not passed:
            details["test_output_tail"] = test_tail[-500:]

        return EvalResult(
            task_id=task.id,
            passed=passed,
            score=1.0 if passed else 0.0,
            details=details,
        )
