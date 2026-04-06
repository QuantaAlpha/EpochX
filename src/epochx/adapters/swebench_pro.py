"""SWE-bench Pro benchmark adapter — real GitHub issues, Docker-based evaluation.

Uses pre-built Docker images from DockerHub (jefzda/sweap-images) and
the standard swebench harness (pip install swebench) for evaluation.
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

# Path to ScaleAI's SWE-bench_Pro-os repo (for run_scripts + eval fallback)
_PRO_REPO = (
    Path(__file__).resolve().parents[3]
    / "benchmarks" / "swebench-pro" / "repo-pro"
)

# DockerHub username for pre-built images
_DOCKERHUB_USER = "jefzda"


def _get_image_uri(instance_id: str, repo: str) -> str:
    """Build DockerHub image URI using ScaleAI's naming convention."""
    pro_helper = _PRO_REPO / "helper_code"
    if pro_helper.exists():
        sys.path.insert(0, str(_PRO_REPO))
        try:
            from helper_code.image_uri import get_dockerhub_image_uri
            return get_dockerhub_image_uri(instance_id, _DOCKERHUB_USER, repo)
        finally:
            sys.path.pop(0)

    # Fallback: manual construction (matches ScaleAI logic)
    repo_base, repo_name = repo.lower().split("/")
    hsh = instance_id.replace("instance_", "")
    if hsh.endswith("-vnan"):
        hsh = hsh[:-5]
    tag = f"{repo_base}.{repo_name}-{hsh}"
    if len(tag) > 128:
        tag = tag[:128]
    return f"{_DOCKERHUB_USER}/sweap-images:{tag}"


@register_adapter
class SWEBenchProAdapter(BenchmarkAdapter):
    """731 real GitHub issues — generate code patches, evaluated via Docker tests."""

    name = "swebench-pro"
    display_name = "SWE-bench Pro"
    description = (
        "731 real GitHub issues — generate code patches, evaluated via Docker tests"
    )
    resource_profile = "medium"

    def __init__(self, dataset_name: str = "ScaleAI/SWE-bench_Pro") -> None:
        self.dataset_name = dataset_name

    @property
    def agent_runtime(self) -> RuntimeType:
        return RuntimeType.DOCKER

    @property
    def eval_runtime(self) -> RuntimeType:
        return RuntimeType.DOCKER

    def _load_rows(self) -> list[dict]:
        """Load dataset rows, using a local JSON cache to avoid repeated HF Hub calls."""
        cache_dir = Path.home() / ".epochx" / "cache"
        cache_file = cache_dir / "swebench-pro.json"

        if cache_file.exists():
            return json.loads(cache_file.read_text())

        try:
            from datasets import load_dataset
        except ImportError:
            raise ImportError(
                "The 'datasets' package is required for SWE-bench Pro. "
                "Install: uv pip install 'epochx[swebench]'"
            )

        dataset = load_dataset(self.dataset_name, split="test")
        rows = [dict(row) for row in dataset]

        # Cache locally
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
            docker_image = _get_image_uri(instance_id, repo)

            prompt = (
                f"You are working on the repository **{repo}** "
                f"(commit `{base_commit}`).\n\n"
                f"## Issue\n{problem_statement}\n\n"
                f"Resolve the issue by editing the source code. "
                f"Your changes will be captured as a `git diff`."
            )

            tasks.append(
                Task(
                    id=f"swebench-pro/{instance_id}",
                    benchmark="swebench-pro",
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
                        "dockerhub_tag": row.get("dockerhub_tag", ""),
                        "before_repo_set_cmd": row.get("before_repo_set_cmd", ""),
                        "selected_test_files_to_run": row.get("selected_test_files_to_run", ""),
                        "fail_to_pass": row.get("fail_to_pass", ""),
                        "pass_to_pass": row.get("pass_to_pass", ""),
                    },
                )
            )

            if limit is not None and len(tasks) >= limit:
                break

        return tasks

    def prepare_image(self, task: Task) -> str | None:
        """Pull pre-built Docker image from DockerHub (jefzda/sweap-images)."""
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

    def collect_output(self, workspace_path: str, task: Task, env=None) -> str:
        """Collect git diff from the container via SSH, or from host workspace.

        Captures all changes: unstaged, staged, and committed since base_commit.
        """
        base_commit = task.metadata.get("base_commit", "")

        if env and env.ssh_host:
            workdir = env.container_workdir or "/testbed"
            # Collect all changes vs base commit (covers unstaged + staged + committed)
            diff_cmd = f"cd {workdir} && git diff {base_commit}" if base_commit else f"cd {workdir} && git diff"
            result = subprocess.run(
                ["ssh", env.ssh_host, diff_cmd],
                capture_output=True, text=True, timeout=60,
            )
            diff = result.stdout
            if not diff.strip() and base_commit:
                # Fallback: try HEAD vs base_commit for committed-only changes
                result = subprocess.run(
                    ["ssh", env.ssh_host, f"cd {workdir} && git diff {base_commit}..HEAD"],
                    capture_output=True, text=True, timeout=60,
                )
                diff = result.stdout
            return diff

        # Fallback: try local git diff (host mode)
        cmd = ["git", "diff", base_commit] if base_commit else ["git", "diff"]
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=workspace_path,
        )
        return result.stdout

    def evaluate(self, task: Task, output: str) -> EvalResult:
        """Evaluate by calling ScaleAI's swe_bench_pro_eval.py --use_local_docker.

        This is the official eval toolchain for SWE-bench Pro. It:
        1. Starts a fresh Docker container with the pre-built image
        2. Applies the patch
        3. Runs the benchmark's test script (run_scripts/{instance_id}/run_script.sh)
        4. Parses test output and compares fail_to_pass / pass_to_pass
        """
        if not output.strip():
            return EvalResult(
                task_id=task.id, passed=False, score=0.0,
                details={"reason": "Empty patch"},
            )

        eval_script = _PRO_REPO / "swe_bench_pro_eval.py"
        scripts_dir = _PRO_REPO / "run_scripts"

        if not eval_script.exists():
            return EvalResult(
                task_id=task.id, passed=False, score=0.0,
                details={
                    "reason": f"Eval script not found: {eval_script}. "
                    "Clone ScaleAI/SWE-bench_Pro-os into benchmarks/swebench-pro/repo-pro/",
                    "patch_lines": len(output.splitlines()),
                },
            )

        instance_id = task.external_id
        if not (scripts_dir / instance_id).exists():
            return EvalResult(
                task_id=task.id, passed=False, score=0.0,
                details={"reason": f"No run_scripts/{instance_id}/ found"},
            )

        try:
            return self._run_eval_script(task, output)
        except Exception as e:
            return EvalResult(
                task_id=task.id, passed=False, score=0.0,
                error=str(e),
                details={"reason": f"Evaluation error: {e}"},
            )

    def _run_eval_script(self, task: Task, patch: str) -> EvalResult:
        """Prepare inputs and call swe_bench_pro_eval.py --use_local_docker."""
        import csv
        import platform as py_platform

        meta = task.metadata
        instance_id = task.external_id

        with tempfile.TemporaryDirectory(prefix="epochx-eval-") as tmpdir:
            tmpdir = Path(tmpdir)
            output_dir = tmpdir / "output"
            output_dir.mkdir()

            # 1. Write raw_sample.csv (one row, columns expected by the eval script)
            csv_path = tmpdir / "raw_sample.csv"
            csv_fields = [
                "instance_id", "repo", "base_commit",
                "before_repo_set_cmd", "selected_test_files_to_run",
                "fail_to_pass", "pass_to_pass", "dockerhub_tag",
            ]
            with open(csv_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=csv_fields)
                writer.writeheader()
                writer.writerow({
                    "instance_id": instance_id,
                    "repo": meta.get("repo", ""),
                    "base_commit": meta.get("base_commit", ""),
                    "before_repo_set_cmd": meta.get("before_repo_set_cmd", ""),
                    "selected_test_files_to_run": meta.get("selected_test_files_to_run", "[]"),
                    "fail_to_pass": meta.get("fail_to_pass", "[]"),
                    "pass_to_pass": meta.get("pass_to_pass", "[]"),
                    "dockerhub_tag": meta.get("dockerhub_tag", ""),
                })

            # 2. Write patch.json
            patch_path = tmpdir / "patch.json"
            patch_path.write_text(json.dumps([{
                "instance_id": instance_id,
                "patch": patch,
            }]))

            # 3. Build command
            cmd = [
                sys.executable, str(_PRO_REPO / "swe_bench_pro_eval.py"),
                "--raw_sample_path", str(csv_path),
                "--patch_path", str(patch_path),
                "--output_dir", str(output_dir),
                "--dockerhub_username", _DOCKERHUB_USER,
                "--scripts_dir", str(_PRO_REPO / "run_scripts"),
                "--use_local_docker",
                "--num_workers", "1",
                "--redo",
            ]

            # Apple Silicon: add platform override
            try:
                if py_platform.machine().lower() in {"arm64", "aarch64"}:
                    cmd.extend(["--docker_platform", "linux/amd64"])
            except Exception:
                pass

            timeout = (task.eval_spec.timeout or 1800) + 300
            print(f"Running swe_bench_pro_eval.py for {instance_id} (timeout: {timeout}s)...", file=sys.stderr)

            # 4. Run the eval script
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(_PRO_REPO),
            )

            if result.returncode != 0:
                print(f"Eval script stderr (last 500 chars):\n{result.stderr[-500:]}", file=sys.stderr)

            # 5. Read eval_results.json
            eval_results_path = output_dir / "eval_results.json"
            if not eval_results_path.exists():
                return EvalResult(
                    task_id=task.id, passed=False, score=0.0,
                    details={
                        "reason": "eval_results.json not produced",
                        "stdout_tail": result.stdout[-500:] if result.stdout else "",
                        "stderr_tail": result.stderr[-500:] if result.stderr else "",
                        "returncode": result.returncode,
                    },
                )

            with open(eval_results_path) as f:
                eval_results = json.load(f)

            passed = eval_results.get(instance_id, False)

            # Try to read detailed test output
            details: dict = {"eval_results": eval_results}
            instance_output = output_dir / instance_id / "_output.json"
            if instance_output.exists():
                try:
                    with open(instance_output) as f:
                        test_output = json.load(f)
                    tests = test_output.get("tests", [])
                    details["tests_total"] = len(tests)
                    details["tests_passed"] = sum(1 for t in tests if t.get("status") == "PASSED")
                    details["tests_failed"] = sum(1 for t in tests if t.get("status") == "FAILED")
                except Exception:
                    pass

            return EvalResult(
                task_id=task.id,
                passed=passed,
                score=1.0 if passed else 0.0,
                details=details,
            )

    def post_setup(self, workspace_path: str, task: Task) -> None:
        """Pre-built images already have the repo at /testbed. No extra setup needed."""
        pass
