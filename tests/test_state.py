"""Tests for run-based StateManager."""

import json
import os

import pytest

from epochx.core.state import EnvironmentState, StateManager


@pytest.fixture
def state_dir(tmp_path):
    return tmp_path / ".epochx"


@pytest.fixture
def sm(state_dir):
    return StateManager(base_dir=str(state_dir))


# ── Run management ─────────────────────────────────────────────


class TestRunManagement:
    def test_create_run(self, sm):
        sm.create_run("swebench-pro", "my-run")
        runs = sm.list_runs()
        assert len(runs) == 1
        assert runs[0]["run_name"] == "my-run"
        assert runs[0]["benchmark"] == "swebench-pro"

    def test_create_run_auto_name(self, sm):
        sm.create_run("swebench-pro")
        runs = sm.list_runs()
        assert len(runs) == 1
        assert runs[0]["run_name"].startswith("swebench-pro-")

    def test_current_run(self, sm):
        sm.create_run("swebench-pro", "run-1")
        assert sm.current_run_name() == "run-1"

        sm.create_run("swebench-pro", "run-2")
        assert sm.current_run_name() == "run-2"

    def test_switch_run(self, sm):
        sm.create_run("swebench-pro", "run-1")
        sm.create_run("swebench-pro", "run-2")
        sm.switch_run("run-1")
        assert sm.current_run_name() == "run-1"

    def test_switch_nonexistent_run(self, sm):
        with pytest.raises(ValueError, match="not found"):
            sm.switch_run("nonexistent")

    def test_get_arena_dir(self, sm, state_dir):
        sm.create_run("swebench-pro", "test-run")
        arena_dir = sm.get_arena_dir()
        assert arena_dir == state_dir / "runs" / "test-run" / "arena"


# ── Environment state ──────────────────────────────────────────


class TestEnvironments:
    def test_save_and_load_environment(self, sm):
        sm.create_run("swebench", "test-run")
        env = EnvironmentState(
            task_id="swebench/django-123",
            benchmark="swebench",
            workspace="/tmp/ws",
            status="running",
            container_id="abc123",
            ssh_port=22000,
            ssh_host="epochx-task-1",
            runtime="docker",
        )
        sm.save_environment(env)
        loaded = sm.get_environment("swebench/django-123")
        assert loaded is not None
        assert loaded.task_id == "swebench/django-123"
        assert loaded.status == "running"
        assert loaded.container_id == "abc123"
        assert loaded.ssh_port == 22000
        assert loaded.started_at != ""

    def test_list_environments(self, sm):
        sm.create_run("swebench", "test-run")
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

    def test_update_status(self, sm):
        sm.create_run("swebench", "test-run")
        env = EnvironmentState(
            task_id="task-1", benchmark="swebench", workspace="/tmp/ws", status="running"
        )
        sm.save_environment(env)
        sm.update_status("task-1", "completed")
        loaded = sm.get_environment("task-1")
        assert loaded is not None
        assert loaded.status == "completed"

    def test_remove_environment(self, sm):
        sm.create_run("swebench", "test-run")
        env = EnvironmentState(
            task_id="task-1", benchmark="swebench", workspace="/tmp/ws", status="running"
        )
        sm.save_environment(env)
        sm.remove_environment("task-1")
        assert sm.get_environment("task-1") is None

    def test_environments_isolated_per_run(self, sm):
        sm.create_run("swebench-pro", "run-1")
        env = EnvironmentState(
            task_id="swebench-pro/task-1",
            benchmark="swebench-pro",
            workspace="/tmp/ws1",
            status="running",
            runtime="docker",
        )
        sm.save_environment(env)

        sm.create_run("swebench-pro", "run-2")
        # run-2 should not see run-1's environments
        loaded = sm.get_environment("swebench-pro/task-1")
        assert loaded is None


# ── Results ────────────────────────────────────────────────────


class TestResults:
    def test_save_and_get_results(self, sm):
        sm.create_run("swebench", "test-run")
        sm.save_result("task-1", {"benchmark": "swebench", "passed": True, "score": 1.0})
        sm.save_result("task-2", {"benchmark": "dabstep", "passed": False, "score": 0.0})

        all_results = sm.get_results()
        assert len(all_results) == 2

        swebench_results = sm.get_results(benchmark="swebench")
        assert len(swebench_results) == 1
        assert "task-1" in swebench_results

    def test_results_isolated_per_run(self, sm):
        sm.create_run("swebench-pro", "run-1")
        sm.save_result("swebench-pro/task-1", {"passed": True, "benchmark": "swebench-pro"})

        sm.create_run("swebench-pro", "run-2")
        results = sm.get_results("swebench-pro")
        assert len(results) == 0


# ── Migration ──────────────────────────────────────────────────


class TestMigration:
    def test_migrate_from_legacy_state(self, state_dir):
        """Old state.json should be auto-migrated to runs/default/."""
        os.makedirs(state_dir, exist_ok=True)
        arena_dir = state_dir / "arena" / "swebench-pro" / "task-1"
        os.makedirs(arena_dir, exist_ok=True)
        (arena_dir / "output.txt").write_text("some output")

        legacy_state = {
            "environments": {
                "swebench-pro/task-1": {
                    "task_id": "swebench-pro/task-1",
                    "benchmark": "swebench-pro",
                    "workspace": "/tmp/ws",
                    "status": "completed",
                    "runtime": "docker",
                    "started_at": "2026-04-08T10:00:00+00:00",
                }
            },
            "results": {
                "swebench-pro/task-1": {
                    "passed": True,
                    "score": 1.0,
                    "benchmark": "swebench-pro",
                }
            },
        }
        with open(state_dir / "state.json", "w") as f:
            json.dump(legacy_state, f)

        sm = StateManager(base_dir=str(state_dir))
        # Should auto-migrate
        assert sm.current_run_name() == "default"
        results = sm.get_results("swebench-pro")
        assert len(results) == 1
        # Old state.json should be gone
        assert not (state_dir / "state.json").exists()
        # Arena dir should be under runs/default/
        assert (
            state_dir / "runs" / "default" / "arena" / "swebench-pro" / "task-1" / "output.txt"
        ).exists()

    def test_no_migration_without_legacy(self, state_dir):
        """If no state.json exists, no migration happens."""
        sm = StateManager(base_dir=str(state_dir))
        assert sm.current_run_name() is None
        assert sm.list_runs() == []
