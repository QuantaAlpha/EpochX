"""Tests for prompt generator."""

from epochx.core.prompt_generator import generate_prompt
from epochx.core.task import (
    EvalSpec,
    EvalType,
    OutputSpec,
    OutputType,
    Task,
    WorkspaceInfo,
    WorkspaceSpec,
    WorkspaceType,
)


def _make_task(**overrides) -> Task:
    defaults = dict(
        id="bench/task-1",
        benchmark="bench",
        external_id="task-1",
        prompt="Fix the bug in main.py",
        workspace=WorkspaceSpec(type=WorkspaceType.GIT_REPO),
        output_spec=OutputSpec(type=OutputType.GIT_DIFF),
        eval_spec=EvalSpec(type=EvalType.DOCKER_TEST, test_command="pytest"),
    )
    defaults.update(overrides)
    return Task(**defaults)


def test_generate_prompt_host_mode():
    task = _make_task()
    ws_info = WorkspaceInfo(path="/tmp/workspace/task-1")

    prompt = generate_prompt(task, ws_info)

    assert "# Task: bench/task-1" in prompt
    assert "Fix the bug in main.py" in prompt
    assert "/tmp/workspace/task-1" in prompt
    assert "epochx bench collect bench/task-1" in prompt
    # Host mode: no SSH
    assert "ssh" not in prompt.lower() or "ssh" not in prompt
    assert "directly on the host" in prompt


def test_generate_prompt_docker_mode():
    task = _make_task()
    ws_info = WorkspaceInfo(
        path="/tmp/workspace/task-1",
        ssh_host="epochx-task-1",
        ssh_port=22000,
        container_id="abc123",
        exec_prefix="ssh epochx-task-1",
    )

    prompt = generate_prompt(task, ws_info)

    assert "# Task: bench/task-1" in prompt
    assert "ssh epochx-task-1" in prompt
    assert "22000" in prompt
    assert "Docker container" in prompt
    assert "/testbed" in prompt


def test_generate_prompt_file_output():
    task = _make_task(
        output_spec=OutputSpec(type=OutputType.FILE_CONTENT, output_file="result.json")
    )
    ws_info = WorkspaceInfo(path="/tmp/workspace/task-1")

    prompt = generate_prompt(task, ws_info)
    assert "result.json" in prompt


def test_generate_prompt_answer_string():
    task = _make_task(
        output_spec=OutputSpec(
            type=OutputType.ANSWER_STRING,
            output_file="answer.txt",
            answer_format="a single number",
        )
    )
    ws_info = WorkspaceInfo(path="/tmp/workspace/task-1")

    prompt = generate_prompt(task, ws_info)
    assert "answer.txt" in prompt
    assert "a single number" in prompt
