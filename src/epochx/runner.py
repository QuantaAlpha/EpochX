"""BenchRunner — orchestrates the full task lifecycle."""

from __future__ import annotations

import json
import subprocess
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from epochx.adapters import get_adapter
from epochx.core.port_manager import PortManager
from epochx.core.prompt_generator import write_prompt
from epochx.core.runtime import RuntimeFactory
from epochx.core.state import EnvironmentState, StateManager
from epochx.core.task import RuntimeType, TaskStatus


class BenchRunner:
    """Orchestrates benchmark task lifecycle: run, collect, grade, stop."""

    def __init__(
        self,
        state: StateManager | None = None,
        port_manager: PortManager | None = None,
    ):
        self.state = state or StateManager()
        self.port_manager = port_manager or PortManager()

    # ------------------------------------------------------------------
    # run_task
    # ------------------------------------------------------------------

    def run_task(
        self,
        benchmark_name: str,
        task_id: str | None = None,
        task_index: int | None = None,
    ) -> dict:
        """Start environment for a single task (interactive mode).

        Resolution order: task_id > task_index > first available task.
        """
        # Auto-create a run if none exists
        if self.state.current_run_name() is None:
            self.state.create_run()

        adapter = get_adapter(benchmark_name)

        # Resolve which task to run
        if task_id is not None:
            tasks = adapter.fetch_tasks(task_ids=[task_id])
            if not tasks:
                return {"status": "error", "message": f"Task {task_id!r} not found in {benchmark_name}"}
        elif task_index is not None:
            tasks = adapter.fetch_tasks()
            if task_index < 0 or task_index >= len(tasks):
                return {"status": "error", "message": f"Task index {task_index} out of range (0-{len(tasks)-1})"}
            tasks = [tasks[task_index]]
        else:
            tasks = adapter.fetch_tasks(limit=1)
            if not tasks:
                return {"status": "error", "message": f"No tasks available for {benchmark_name}"}

        task = tasks[0]

        # Check if already running
        existing = self.state.get_environment(task.id)
        if existing and existing.status == TaskStatus.RUNNING.value:
            return {
                "status": "already_running",
                "task_id": task.id,
                "workspace": existing.workspace,
                "message": f"Task {task.id} is already running.",
                "next_command": f"epochx-bench collect {task.id}",
            }

        # Prepare Docker image if needed
        if task.workspace.runtime == RuntimeType.DOCKER:
            try:
                image = adapter.prepare_image(task)
                if image:
                    task.workspace.docker_image = image  # Use the prepared image
            except RuntimeError as e:
                return {"status": "error", "message": f"Failed to prepare Docker image: {e}"}

        # Create runtime and setup workspace
        arena_dir = self.state.get_arena_dir()
        runtime = RuntimeFactory.create(
            task.workspace.runtime,
            base_dir=arena_dir,
            port_manager=self.port_manager,
            docker_image=task.workspace.docker_image or "python:3.11-slim",
        )
        ws_info = runtime.setup(task.id, task.workspace)

        # Post-setup hook (e.g. copy context files)
        adapter.post_setup(ws_info.path, task)

        # Write prompt
        prompt_path = write_prompt(task, ws_info)

        # Write meta.json
        epochx_dir = Path(ws_info.path) / ".epochx"
        epochx_dir.mkdir(parents=True, exist_ok=True)
        meta = {
            "task_id": task.id,
            "benchmark": task.benchmark,
            "external_id": task.external_id,
            "runtime": task.workspace.runtime.value,
            "started_at": datetime.now(timezone.utc).isoformat(),
        }
        (epochx_dir / "meta.json").write_text(json.dumps(meta, indent=2))

        # Save environment state
        env = EnvironmentState(
            task_id=task.id,
            benchmark=task.benchmark,
            workspace=ws_info.path,
            status=TaskStatus.RUNNING.value,
            container_id=ws_info.container_id,
            ssh_port=ws_info.ssh_port,
            ssh_host=ws_info.ssh_host,
            container_workdir=ws_info.container_workdir,
            runtime=task.workspace.runtime.value,
        )
        self.state.save_environment(env)

        return {
            "status": "started",
            "task_id": task.id,
            "benchmark": task.benchmark,
            "workspace": ws_info.path,
            "prompt_file": str(prompt_path),
            "next_command": f"epochx-bench collect {task.id}",
        }

    # ------------------------------------------------------------------
    # collect_task
    # ------------------------------------------------------------------

    def collect_task(self, task_id: str) -> dict:
        """Collect agent output for a running task."""
        env = self.state.get_environment(task_id)
        if env is None:
            return {"status": "error", "message": f"No running environment for {task_id!r}"}

        adapter = get_adapter(env.benchmark)
        ext_id = self._to_external_id(task_id, env.benchmark)
        tasks = adapter.fetch_tasks(task_ids=[ext_id])
        if not tasks:
            return {"status": "error", "message": f"Task {task_id!r} not found in {env.benchmark}"}

        task = tasks[0]
        output = adapter.collect_output(env.workspace, task, env=env)

        # Write output to .epochx/output.txt
        epochx_dir = Path(env.workspace) / ".epochx"
        epochx_dir.mkdir(parents=True, exist_ok=True)
        output_path = epochx_dir / "output.txt"
        output_path.write_text(output)

        # Collect trajectory
        trajectory = self._collect_trajectory(env)
        if trajectory:
            (epochx_dir / "trajectory_collected.json").write_text(
                json.dumps(trajectory, ensure_ascii=False, indent=2)
            )

        # Update status
        self.state.update_status(task_id, TaskStatus.COLLECTING.value)

        truncated = output[:500] + ("..." if len(output) > 500 else "")
        result = {
            "status": "collected",
            "task_id": task_id,
            "output_type": task.output_spec.type.value,
            "content": truncated,
            "saved_to": str(output_path),
            "next_command": f"epochx-bench grade {task_id}",
        }
        if trajectory:
            result["trajectory_steps"] = len(trajectory)
        return result

    # ------------------------------------------------------------------
    # grade_task
    # ------------------------------------------------------------------

    def grade_task(self, task_id: str) -> dict:
        """Evaluate collected output for a task."""
        env = self.state.get_environment(task_id)
        if env is None:
            return {"status": "error", "message": f"No environment for {task_id!r}"}

        # Read output
        output_path = Path(env.workspace) / ".epochx" / "output.txt"
        if not output_path.exists():
            return {
                "status": "error",
                "message": f"No output collected. Run: epochx-bench collect {task_id}",
            }
        output = output_path.read_text()

        adapter = get_adapter(env.benchmark)
        ext_id = self._to_external_id(task_id, env.benchmark)
        tasks = adapter.fetch_tasks(task_ids=[ext_id])
        if not tasks:
            return {"status": "error", "message": f"Task {task_id!r} not found in {env.benchmark}"}

        task = tasks[0]
        result = adapter.evaluate(task, output)

        # Save result to task's own .epochx/result.json
        result_dict = asdict(result)
        result_dict["benchmark"] = env.benchmark

        # Attach trajectory if collected
        traj_path = Path(env.workspace) / ".epochx" / "trajectory_collected.json"
        if traj_path.exists():
            try:
                result_dict["trajectory"] = json.loads(traj_path.read_text())
            except Exception:
                pass

        # Attach output
        output_path_for_result = Path(env.workspace) / ".epochx" / "output.txt"
        if output_path_for_result.exists():
            result_dict["output"] = output_path_for_result.read_text()

        result_path = Path(env.workspace) / ".epochx" / "result.json"
        result_path.write_text(json.dumps(result_dict, indent=2))

        # Also save to global state for status tracking
        self.state.save_result(task_id, result_dict)

        # Update status
        new_status = TaskStatus.COMPLETED.value if result.passed else TaskStatus.FAILED.value
        self.state.update_status(task_id, new_status)

        return {
            "status": "graded",
            "task_id": task_id,
            "passed": result.passed,
            "score": result.score,
            "details": result.details,
            "result_file": str(result_path),
            "next_command": f"epochx-bench stop {task_id}",
        }

    # ------------------------------------------------------------------
    # stop_task
    # ------------------------------------------------------------------

    def stop_task(self, task_id: str) -> dict:
        """Stop a running task: kill container if docker, release port, update state."""
        env = self.state.get_environment(task_id)
        if env is None:
            return {"status": "error", "message": f"No environment for {task_id!r}"}

        # Teardown Docker container if applicable
        if env.container_id:
            try:
                import docker as docker_lib

                client = docker_lib.from_env()
                container = client.containers.get(env.container_id)
                container.stop(timeout=5)
            except Exception:
                pass

        # Release port
        self.port_manager.release(task_id)

        # Update state
        self.state.update_status(task_id, TaskStatus.STOPPED.value)

        return {
            "status": "stopped",
            "task_id": task_id,
            "message": f"Task {task_id} stopped and cleaned up.",
        }

    # ------------------------------------------------------------------
    # get_next_task
    # ------------------------------------------------------------------

    def get_next_task(self, benchmark_name: str) -> dict:
        """Get next pending task (not completed, not running)."""
        adapter = get_adapter(benchmark_name)
        all_tasks = adapter.fetch_tasks()

        # Get completed/running task IDs
        results = self.state.get_results(benchmark=benchmark_name)
        running_envs = self.state.list_environments(status=TaskStatus.RUNNING.value)
        running_ids = {e.task_id for e in running_envs}
        completed_ids = set(results.keys())
        skip_ids = running_ids | completed_ids

        remaining = [t for t in all_tasks if t.id not in skip_ids]

        if not remaining:
            return {
                "status": "all_done",
                "total": len(all_tasks),
                "remaining": 0,
                "message": f"All {len(all_tasks)} tasks completed or in progress.",
            }

        next_task = remaining[0]
        return {
            "status": "found",
            "task_id": next_task.id,
            "total": len(all_tasks),
            "remaining": len(remaining),
            "start_command": f"epochx-bench run {benchmark_name} --task {next_task.external_id}",
        }

    def _collect_trajectory(self, env: EnvironmentState) -> list[dict]:
        """Collect trajectory from multiple sources, merge into one list.

        Sources (in priority order):
        1. /.epochx/trajectory.jsonl  — agent-written rich trajectory
        2. /.epochx/ssh_log.jsonl     — auto-recorded SSH commands
        3. git log inside container    — fallback: extract commits as steps
        """
        epochx_dir = Path(env.workspace) / ".epochx"
        trajectory: list[dict] = []

        # Source 1: agent-written trajectory
        agent_traj_path = epochx_dir / "trajectory.jsonl"
        if agent_traj_path.exists():
            for line in agent_traj_path.read_text().splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    trajectory.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        # Source 2: SSH command log (from host-side runtime.exec logging)
        ssh_log_path = epochx_dir / "ssh_log.jsonl"
        if ssh_log_path.exists():
            step = len(trajectory)
            for line in ssh_log_path.read_text().splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                step += 1
                trajectory.append({
                    "step": step,
                    "type": "tool_call",
                    "tool_name": "shell",
                    "tool_input": entry.get("cmd", ""),
                    "tool_output": entry.get("output", "")[:500],
                    "duration_ms": entry.get("ms"),
                    "content": f"[auto-logged] {entry.get('ts', '')}",
                    "source": "ssh_log",
                })

        # Source 3: git log fallback
        if not trajectory and env.ssh_host:
            workdir = env.container_workdir or "/testbed"
            try:
                result = subprocess.run(
                    ["ssh", env.ssh_host,
                     f"cd {workdir} && git log --oneline --reverse --format='%H|%s|%ai' 2>/dev/null | tail -20"],
                    capture_output=True, text=True, timeout=15,
                )
                step = 0
                for line in result.stdout.strip().splitlines():
                    parts = line.split("|", 2)
                    if len(parts) < 2:
                        continue
                    step += 1
                    trajectory.append({
                        "step": step,
                        "type": "action",
                        "tool_name": "git_commit",
                        "content": parts[1],
                        "tool_input": parts[0][:12],
                        "source": "git_log",
                    })
                result2 = subprocess.run(
                    ["ssh", env.ssh_host,
                     f"cd {workdir} && git diff --stat HEAD~1 HEAD 2>/dev/null || true"],
                    capture_output=True, text=True, timeout=15,
                )
                if result2.stdout.strip() and trajectory:
                    trajectory.append({
                        "step": step + 1,
                        "type": "observation",
                        "content": f"Changes: {result2.stdout.strip()}",
                        "source": "git_log",
                    })
            except Exception:
                pass

        return trajectory

    @staticmethod
    def _to_external_id(task_id: str, benchmark: str) -> str:
        """Strip benchmark prefix from full task ID to get external_id.

        e.g. "dabstep/5" with benchmark="dabstep" -> "5"
        If no prefix matches, return as-is.
        """
        prefix = f"{benchmark}/"
        if task_id.startswith(prefix):
            return task_id[len(prefix):]
        return task_id
