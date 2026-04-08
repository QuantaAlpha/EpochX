"""SWE-bench Verified adapter — 500 human-validated GitHub issues, standard swebench eval.

Uses the official swebench Docker images (swebench/ namespace on DockerHub)
and the standard swebench harness (pip install swebench) for evaluation.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
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


# Build number used by the SWE-bench team on DockerHub
_SWEBENCH_BUILD_NUM = "1776"


def _get_image_name(instance_id: str) -> str:
    """Build Docker image name using swebench DockerHub naming convention.

    instance_id like "django__django-10097" becomes
    "swebench/sweb.eval.x86_64.django_1776_django-10097:latest"
    """
    # Replace __ with _{build_num}_ for the DockerHub naming convention
    dockerhub_id = instance_id.replace("__", f"_{_SWEBENCH_BUILD_NUM}_")
    return f"swebench/sweb.eval.x86_64.{dockerhub_id}:latest"


@register_adapter
class SWEBenchVerifiedAdapter(BenchmarkAdapter):
    """500 human-validated GitHub issues — generate code patches, evaluated via Docker tests."""

    name = "swebench-verified"
    display_name = "SWE-bench Verified"
    description = (
        "500 human-validated GitHub issues — generate code patches, "
        "evaluated via standard swebench harness"
    )
    resource_profile = "medium"

    def __init__(self, dataset_name: str = "princeton-nlp/SWE-bench_Verified") -> None:
        self.dataset_name = dataset_name

    @property
    def agent_runtime(self) -> RuntimeType:
        return RuntimeType.DOCKER

    @property
    def eval_runtime(self) -> RuntimeType:
        return RuntimeType.DOCKER

    def _load_rows(self) -> list[dict]:
        """Load dataset rows, using a local JSON cache."""
        cache_dir = Path.home() / ".epochx" / "cache"
        cache_file = cache_dir / "swebench-verified.json"

        if cache_file.exists():
            return json.loads(cache_file.read_text())

        try:
            from datasets import load_dataset
        except ImportError:
            raise ImportError(
                "The 'datasets' package is required for SWE-bench Verified. "
                "Install: uv pip install 'epochx[swebench]'"
            )

        dataset = load_dataset(self.dataset_name, split="test")
        rows = [dict(row) for row in dataset]

        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps(rows, ensure_ascii=False))

        return rows

    def fetch_tasks(
        self,
        limit: int | None = None,
        task_ids: list[str] | None = None,
    ) -> list[Task]:
        rows = self._load_rows()

        tasks: list[Task] = []
        for row in rows:
            instance_id: str = row["instance_id"]
            if task_ids is not None and instance_id not in task_ids:
                continue

            repo: str = row["repo"]
            base_commit: str = row["base_commit"]
            problem_statement: str = row["problem_statement"]
            version: str = row.get("version", "")
            docker_image = _get_image_name(instance_id)

            prompt = (
                f"You are working on the repository **{repo}** "
                f"(commit `{base_commit}`).\n\n"
                f"## Issue\n{problem_statement}\n\n"
                f"Resolve the issue by editing the source code. "
                f"Your changes will be captured as a `git diff`."
            )

            tasks.append(
                Task(
                    id=f"swebench-verified/{instance_id}",
                    benchmark="swebench-verified",
                    external_id=instance_id,
                    prompt=prompt,
                    workspace=WorkspaceSpec(
                        type=WorkspaceType.GIT_REPO,
                        repo_url=f"https://github.com/{repo}.git",
                        base_commit=base_commit,
                        runtime=RuntimeType.DOCKER,
                        docker_image=docker_image,
                    ),
                    output_spec=OutputSpec(type=OutputType.GIT_DIFF),
                    eval_spec=EvalSpec(type=EvalType.DOCKER_TEST, timeout=1800),
                    metadata={
                        "repo": repo,
                        "instance_id": instance_id,
                        "base_commit": base_commit,
                        "version": version,
                        "FAIL_TO_PASS": row.get("FAIL_TO_PASS", ""),
                        "PASS_TO_PASS": row.get("PASS_TO_PASS", ""),
                        "environment_setup_commit": row.get("environment_setup_commit", ""),
                        "difficulty": row.get("difficulty", ""),
                    },
                )
            )

            if limit is not None and len(tasks) >= limit:
                break

        return tasks

    def prepare_image(self, task: Task) -> str | None:
        """Pull pre-built Docker image from swebench namespace on DockerHub."""
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

    def _find_diff_base(self, base_commit: str, env, workdir: str) -> str:
        """Find the SWE-bench setup commit to use as diff base.

        SWE-bench images contain a setup commit (author "SWE-bench") on top of
        base_commit that modifies build configs (e.g. pinning setuptools).
        Diffing from base_commit would include those changes, causing patch
        apply failures during evaluation.  Use the setup commit instead.

        See also: https://github.com/SWE-agent/SWE-agent/issues/810
        """
        if not base_commit:
            return ""
        if env and env.ssh_host:
            find_cmd = (
                f"cd {workdir} && "
                f"git log --format='%H' --author='SWE-bench' "
                f"--reverse {base_commit}..HEAD 2>/dev/null | head -1"
            )
            result = subprocess.run(
                ["ssh", env.ssh_host, find_cmd],
                capture_output=True, text=True, timeout=30,
            )
            setup_commit = result.stdout.strip()
            if setup_commit:
                return setup_commit
        return base_commit

    def collect_output(self, workspace_path: str, task: Task, env=None) -> str:
        """Collect git diff from the container via SSH.

        Uses the SWE-bench setup commit (if present) as the diff base to avoid
        including environment setup changes in the patch.
        Falls back to base_commit if no setup commit is found.
        """
        base_commit = task.metadata.get("base_commit", "")

        if env and env.ssh_host:
            workdir = env.container_workdir or "/testbed"
            diff_base = self._find_diff_base(base_commit, env, workdir)
            diff_cmd = (
                f"cd {workdir} && git diff {diff_base}"
                if diff_base
                else f"cd {workdir} && git diff"
            )
            result = subprocess.run(
                ["ssh", env.ssh_host, diff_cmd],
                capture_output=True, text=True, timeout=60,
            )
            diff = result.stdout
            if not diff.strip() and diff_base:
                result = subprocess.run(
                    ["ssh", env.ssh_host, f"cd {workdir} && git diff {diff_base}..HEAD"],
                    capture_output=True, text=True, timeout=60,
                )
                diff = result.stdout
            return diff

        # Fallback: try local git diff
        cmd = ["git", "diff", base_commit] if base_commit else ["git", "diff"]
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=workspace_path,
        )
        return result.stdout

    def evaluate(self, task: Task, output: str) -> EvalResult:
        """Evaluate using the standard swebench harness.

        Calls: python -m swebench.harness.run_evaluation
        """
        if not output.strip():
            return EvalResult(
                task_id=task.id, passed=False, score=0.0,
                details={"reason": "Empty patch"},
            )

        instance_id = task.external_id

        try:
            return self._run_swebench_eval(task, output)
        except Exception as e:
            return EvalResult(
                task_id=task.id, passed=False, score=0.0,
                error=str(e),
                details={"reason": f"Evaluation error: {e}"},
            )

    def _run_swebench_eval(self, task: Task, patch: str) -> EvalResult:
        """Run the standard swebench harness evaluation."""
        instance_id = task.external_id

        with tempfile.TemporaryDirectory(prefix="epochx-eval-swebv-") as tmpdir:
            tmpdir = Path(tmpdir)

            # Write predictions file
            predictions_path = tmpdir / "predictions.jsonl"
            pred = {
                "instance_id": instance_id,
                "model_name_or_path": "epochx-agent",
                "model_patch": patch,
            }
            predictions_path.write_text(json.dumps(pred) + "\n")

            # Build command
            cmd = [
                sys.executable, "-m", "swebench.harness.run_evaluation",
                "--dataset_name", self.dataset_name,
                "--predictions_path", str(predictions_path),
                "--max_workers", "1",
                "--instance_ids", instance_id,
                "--run_id", "epochx-eval",
            ]

            timeout = (task.eval_spec.timeout or 1800) + 300
            print(
                f"Running swebench eval for {instance_id} (timeout: {timeout}s)...",
                file=sys.stderr,
            )

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(tmpdir),
            )

            if result.returncode != 0:
                print(
                    f"Eval stderr (last 500 chars):\n{result.stderr[-500:]}",
                    file=sys.stderr,
                )

            # Parse results from the swebench output
            return self._parse_eval_results(result, instance_id, tmpdir)

    def _parse_eval_results(
        self, proc_result, instance_id: str, tmpdir: Path
    ) -> EvalResult:
        """Parse swebench harness evaluation results."""
        stdout = proc_result.stdout or ""

        # Strategy 1: Look for the JSON report file written by the harness.
        # Format: {model_name}.{run_id}.json (e.g., epochx-agent.epochx-eval.json)
        report_candidates = list(tmpdir.glob("*.epochx-eval.json"))
        if not report_candidates:
            # Also check common log paths
            report_candidates = list(tmpdir.glob("logs/**/*.json"))

        for report_path in report_candidates:
            try:
                report = json.loads(report_path.read_text())
                # The report has "resolved", "unresolved", etc. as lists
                if isinstance(report, dict):
                    # swebench v2 schema uses "resolved_ids"
                    resolved_list = report.get("resolved_ids", report.get("resolved", []))
                    if isinstance(resolved_list, list):
                        resolved = instance_id in resolved_list
                        return EvalResult(
                            task_id=f"swebench-verified/{instance_id}",
                            passed=resolved,
                            score=1.0 if resolved else 0.0,
                            details={"report": report, "report_file": str(report_path)},
                        )
            except (json.JSONDecodeError, OSError):
                continue

        # Strategy 2: Parse stdout for "Instances resolved: N"
        resolved_from_stdout = False
        for line in stdout.splitlines():
            if "Instances resolved:" in line:
                try:
                    count = int(line.split(":")[-1].strip())
                    resolved_from_stdout = count > 0
                except ValueError:
                    pass

        if resolved_from_stdout:
            return EvalResult(
                task_id=f"swebench-verified/{instance_id}",
                passed=True,
                score=1.0,
                details={"reason": "Parsed from stdout: resolved", "stdout_tail": stdout[-500:]},
            )

        # Strategy 3: Check for unresolved indication
        for line in stdout.splitlines():
            if "Instances unresolved:" in line:
                try:
                    count = int(line.split(":")[-1].strip())
                    if count > 0:
                        return EvalResult(
                            task_id=f"swebench-verified/{instance_id}",
                            passed=False,
                            score=0.0,
                            details={"reason": "Parsed from stdout: unresolved", "stdout_tail": stdout[-500:]},
                        )
                except ValueError:
                    pass

        return EvalResult(
            task_id=f"swebench-verified/{instance_id}",
            passed=False,
            score=0.0,
            details={
                "reason": "Could not parse evaluation results",
                "stdout_tail": stdout[-500:] if stdout else "",
                "stderr_tail": (proc_result.stderr or "")[-500:],
                "returncode": proc_result.returncode,
            },
        )

    def post_setup(self, workspace_path: str, task: Task) -> None:
        """Pre-built images already have the repo at /testbed. No extra setup needed."""
        pass
