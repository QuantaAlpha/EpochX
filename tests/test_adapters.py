"""Tests for BenchmarkAdapter base, registry, and DABstep adapter."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from epochx.adapters.base import (
    BenchmarkAdapter,
    _REGISTRY,
    get_adapter,
    list_adapters,
    register_adapter,
)
from epochx.adapters.dabstep import DABstepAdapter
from epochx.core.task import EvalType, OutputType, RuntimeType, WorkspaceType


# ── helpers ──────────────────────────────────────────────────────────────


def _make_dabstep_data(tmp: str) -> str:
    """Create minimal DABstep data layout for testing.

    Returns the data_dir path (parent of tasks/ and context/).
    """
    data_dir = Path(tmp) / "data"
    tasks_dir = data_dir / "tasks"
    context_dir = data_dir / "context"
    tasks_dir.mkdir(parents=True)
    context_dir.mkdir(parents=True)

    rows = [
        {
            "task_id": "1",
            "question": "What is 2+2?",
            "guidelines": "Answer with a number.",
            "level": "easy",
            "answer": "4",
        },
        {
            "task_id": "2",
            "question": "Capital of France?",
            "guidelines": "Answer with a city name.",
            "level": "easy",
            "answer": "Paris",
        },
    ]
    with open(tasks_dir / "dev.jsonl", "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")

    (context_dir / "sample.csv").write_text("col_a,col_b\n1,2\n")
    return str(data_dir)


# ── registry tests ───────────────────────────────────────────────────────


def test_dabstep_registered():
    """DABstep adapter is auto-registered via the decorator."""
    assert "dabstep" in _REGISTRY


def test_get_adapter_returns_instance():
    adapter = get_adapter("dabstep")
    assert isinstance(adapter, DABstepAdapter)


def test_get_adapter_unknown_raises():
    with pytest.raises(KeyError, match="Unknown adapter"):
        get_adapter("nonexistent_benchmark_xyz")


def test_list_adapters_includes_dabstep():
    infos = list_adapters()
    names = [i["name"] for i in infos]
    assert "dabstep" in names


def test_adapter_info_fields():
    adapter = DABstepAdapter()
    info = adapter.info()
    assert info["name"] == "dabstep"
    assert info["display_name"] == "DABstep"
    assert info["agent_runtime"] == "host"
    assert info["eval_runtime"] == "host"
    assert info["resource_profile"] == "light"


# ── DABstep fetch_tasks ─────────────────────────────────────────────────


def test_dabstep_fetch_tasks(tmp_path: Path):
    data_dir = _make_dabstep_data(str(tmp_path))
    adapter = DABstepAdapter(data_dir=data_dir)
    tasks = adapter.fetch_tasks()

    assert len(tasks) == 2
    assert tasks[0].id == "dabstep/1"
    assert tasks[1].id == "dabstep/2"
    assert tasks[0].benchmark == "dabstep"
    assert tasks[0].external_id == "1"
    assert tasks[0].workspace.type == WorkspaceType.DATA_DIR
    assert tasks[0].workspace.runtime == RuntimeType.HOST
    assert tasks[0].output_spec.type == OutputType.ANSWER_STRING
    assert tasks[0].eval_spec.type == EvalType.EXACT_MATCH
    assert tasks[0].eval_spec.expected_answer == "4"
    assert tasks[0].metadata["level"] == "easy"


def test_dabstep_fetch_tasks_with_limit(tmp_path: Path):
    data_dir = _make_dabstep_data(str(tmp_path))
    adapter = DABstepAdapter(data_dir=data_dir)
    tasks = adapter.fetch_tasks(limit=1)
    assert len(tasks) == 1


def test_dabstep_fetch_tasks_with_ids(tmp_path: Path):
    data_dir = _make_dabstep_data(str(tmp_path))
    adapter = DABstepAdapter(data_dir=data_dir)
    tasks = adapter.fetch_tasks(task_ids=["2"])
    assert len(tasks) == 1
    assert tasks[0].external_id == "2"


# ── DABstep evaluate ────────────────────────────────────────────────────


def test_dabstep_evaluate_correct(tmp_path: Path):
    data_dir = _make_dabstep_data(str(tmp_path))
    adapter = DABstepAdapter(data_dir=data_dir)
    task = adapter.fetch_tasks(task_ids=["1"])[0]

    result = adapter.evaluate(task, "4")
    assert result.passed is True
    assert result.score == 1.0
    assert result.task_id == "dabstep/1"


def test_dabstep_evaluate_wrong(tmp_path: Path):
    data_dir = _make_dabstep_data(str(tmp_path))
    adapter = DABstepAdapter(data_dir=data_dir)
    task = adapter.fetch_tasks(task_ids=["1"])[0]

    result = adapter.evaluate(task, "5")
    assert result.passed is False
    assert result.score == 0.0


def test_dabstep_evaluate_strips_whitespace(tmp_path: Path):
    data_dir = _make_dabstep_data(str(tmp_path))
    adapter = DABstepAdapter(data_dir=data_dir)
    task = adapter.fetch_tasks(task_ids=["1"])[0]

    result = adapter.evaluate(task, "  4\n")
    assert result.passed is True


# ── DABstep collect_output ──────────────────────────────────────────────


def test_dabstep_collect_output(tmp_path: Path):
    data_dir = _make_dabstep_data(str(tmp_path))
    adapter = DABstepAdapter(data_dir=data_dir)
    task = adapter.fetch_tasks(task_ids=["1"])[0]

    ws = tmp_path / "workspace"
    ws.mkdir()
    (ws / ".epochx").mkdir()
    (ws / ".epochx" / "answer.txt").write_text("  4\n")

    output = adapter.collect_output(str(ws), task)
    assert output == "4"


def test_dabstep_collect_output_missing(tmp_path: Path):
    data_dir = _make_dabstep_data(str(tmp_path))
    adapter = DABstepAdapter(data_dir=data_dir)
    task = adapter.fetch_tasks(task_ids=["1"])[0]

    ws = tmp_path / "workspace_empty"
    ws.mkdir()
    output = adapter.collect_output(str(ws), task)
    assert output == ""


# ── DABstep post_setup ──────────────────────────────────────────────────


def test_dabstep_post_setup_copies_context(tmp_path: Path):
    data_dir = _make_dabstep_data(str(tmp_path))
    adapter = DABstepAdapter(data_dir=data_dir)
    task = adapter.fetch_tasks(task_ids=["1"])[0]

    ws = tmp_path / "workspace"
    ws.mkdir()
    adapter.post_setup(str(ws), task)

    copied = ws / "data" / "sample.csv"
    assert copied.exists()
    assert "col_a" in copied.read_text()
