"""Tests for StateManager."""

from pathlib import Path

from epochx.core.state import EnvironmentState, StateManager


def test_save_and_load_environment(tmp_path: Path):
    sm = StateManager(state_file=tmp_path / "state.json")
    env = EnvironmentState(
        task_id="task-1",
        benchmark="swebench",
        workspace="/tmp/ws",
        status="running",
        container_id="abc123",
        ssh_port=22000,
        ssh_host="epochx-task-1",
        runtime="docker",
    )
    sm.save_environment(env)

    loaded = sm.get_environment("task-1")
    assert loaded is not None
    assert loaded.task_id == "task-1"
    assert loaded.benchmark == "swebench"
    assert loaded.status == "running"
    assert loaded.container_id == "abc123"
    assert loaded.ssh_port == 22000
    assert loaded.started_at != ""


def test_list_environments(tmp_path: Path):
    sm = StateManager(state_file=tmp_path / "state.json")
    env1 = EnvironmentState(
        task_id="task-1", benchmark="swebench", workspace="/tmp/ws1", status="running"
    )
    env2 = EnvironmentState(
        task_id="task-2", benchmark="dabstep", workspace="/tmp/ws2", status="completed"
    )
    sm.save_environment(env1)
    sm.save_environment(env2)

    all_envs = sm.list_environments()
    assert len(all_envs) == 2

    running = sm.list_environments(status="running")
    assert len(running) == 1
    assert running[0].task_id == "task-1"


def test_remove_environment(tmp_path: Path):
    sm = StateManager(state_file=tmp_path / "state.json")
    env = EnvironmentState(
        task_id="task-1", benchmark="swebench", workspace="/tmp/ws", status="running"
    )
    sm.save_environment(env)
    sm.remove_environment("task-1")
    assert sm.get_environment("task-1") is None


def test_update_status(tmp_path: Path):
    sm = StateManager(state_file=tmp_path / "state.json")
    env = EnvironmentState(
        task_id="task-1", benchmark="swebench", workspace="/tmp/ws", status="running"
    )
    sm.save_environment(env)
    sm.update_status("task-1", "completed")
    loaded = sm.get_environment("task-1")
    assert loaded is not None
    assert loaded.status == "completed"


def test_save_and_get_results(tmp_path: Path):
    sm = StateManager(state_file=tmp_path / "state.json")
    sm.save_result("task-1", {"benchmark": "swebench", "passed": True, "score": 1.0})
    sm.save_result("task-2", {"benchmark": "dabstep", "passed": False, "score": 0.0})

    all_results = sm.get_results()
    assert len(all_results) == 2

    swebench_results = sm.get_results(benchmark="swebench")
    assert len(swebench_results) == 1
    assert "task-1" in swebench_results
