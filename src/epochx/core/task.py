"""Standardized Task model for all benchmarks."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class WorkspaceType(str, Enum):
    GIT_REPO = "git_repo"
    DATA_DIR = "data_dir"
    MCP_ENV = "mcp_env"
    API_ONLY = "api_only"


class OutputType(str, Enum):
    GIT_DIFF = "git_diff"
    FILE_CONTENT = "file_content"
    ANSWER_STRING = "answer_string"
    TRAJECTORY = "trajectory"
    SNAPSHOT_DIFF = "snapshot_diff"


class EvalType(str, Enum):
    DOCKER_TEST = "docker_test"
    EXACT_MATCH = "exact_match"
    LLM_JUDGE = "llm_judge"
    REWARD_FUNCTION = "reward_function"
    CUSTOM_SCRIPT = "custom_script"


class RuntimeType(str, Enum):
    HOST = "host"
    UV = "uv"
    DOCKER = "docker"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COLLECTING = "collecting"
    GRADING = "grading"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


@dataclass
class WorkspaceSpec:
    """Workspace definition - where and how the agent works."""

    type: WorkspaceType

    # git_repo type
    repo_url: str | None = None
    base_commit: str | None = None

    # data_dir type
    data_files: list[str] | None = None
    data_source: str | None = None

    # Runtime requirements
    runtime: RuntimeType = RuntimeType.HOST
    docker_image: str | None = None
    python_version: str | None = None
    system_deps: list[str] = field(default_factory=list)

    # Hints for prompt generation
    available_commands: list[str] = field(default_factory=list)


@dataclass
class OutputSpec:
    """How to collect the agent's output."""

    type: OutputType

    # file_content / answer_string
    output_file: str | None = None

    # answer_string format hint
    answer_format: str | None = None


@dataclass
class EvalSpec:
    """How to evaluate the agent's output."""

    type: EvalType

    # docker_test
    test_command: str | None = None

    # exact_match
    expected_answer: str | None = None

    # llm_judge
    rubric: list[dict[str, Any]] | None = None
    judge_model: str | None = None

    # reward_function / custom_script
    eval_script: str | None = None

    # General
    timeout: int = 1800


@dataclass
class Task:
    """Standardized task across all benchmarks."""

    # Identity
    id: str  # "swebench-pro/django__django-16379"
    benchmark: str  # "swebench-pro"
    external_id: str  # "django__django-16379"

    # Input
    prompt: str  # Full task description for the agent

    # Workspace
    workspace: WorkspaceSpec

    # Output
    output_spec: OutputSpec

    # Evaluation
    eval_spec: EvalSpec

    # Extra benchmark-specific fields
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvalResult:
    """Evaluation result for a task."""

    task_id: str
    passed: bool
    score: float  # 0.0 - 1.0
    details: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


@dataclass
class WorkspaceInfo:
    """Runtime workspace info returned after setup."""

    path: str  # Local workspace path
    ssh_host: str | None = None  # SSH host alias (Docker mode)
    ssh_port: int | None = None  # SSH port (Docker mode)
    container_id: str | None = None  # Docker container ID
    exec_prefix: str = "bash -c"  # Command execution prefix
    container_workdir: str | None = None  # Working directory inside container
