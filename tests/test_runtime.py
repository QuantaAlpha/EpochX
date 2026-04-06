"""Tests for Runtime layer (host runtime only, Docker requires Docker daemon)."""

from pathlib import Path

from epochx.core.runtime import ExecResult, HostRuntime, RuntimeFactory
from epochx.core.task import RuntimeType, WorkspaceSpec, WorkspaceType


def test_host_runtime_setup_creates_workspace(tmp_path: Path):
    rt = HostRuntime(base_dir=tmp_path)
    ws_spec = WorkspaceSpec(type=WorkspaceType.DATA_DIR)
    info = rt.setup("test-task", ws_spec)

    assert Path(info.path).exists()
    assert (Path(info.path) / ".epochx").exists()
    assert info.ssh_host is None
    assert info.ssh_port is None
    assert info.container_id is None
    assert info.exec_prefix == "bash -c"


def test_host_runtime_exec(tmp_path: Path):
    rt = HostRuntime(base_dir=tmp_path)
    ws_spec = WorkspaceSpec(type=WorkspaceType.DATA_DIR)
    rt.setup("test-task", ws_spec)

    result = rt.exec("echo hello")
    assert isinstance(result, ExecResult)
    assert result.returncode == 0
    assert result.stdout.strip() == "hello"
    assert result.stderr == ""


def test_host_runtime_exec_failure(tmp_path: Path):
    rt = HostRuntime(base_dir=tmp_path)
    ws_spec = WorkspaceSpec(type=WorkspaceType.DATA_DIR)
    rt.setup("test-task", ws_spec)

    result = rt.exec("exit 1")
    assert result.returncode == 1


def test_host_runtime_teardown(tmp_path: Path):
    rt = HostRuntime(base_dir=tmp_path)
    ws_spec = WorkspaceSpec(type=WorkspaceType.DATA_DIR)
    info = rt.setup("test-task", ws_spec)
    rt.teardown()
    # Workspace should still exist after teardown (no-op)
    assert Path(info.path).exists()


def test_runtime_factory_host(tmp_path: Path):
    rt = RuntimeFactory.create(RuntimeType.HOST, base_dir=tmp_path)
    assert isinstance(rt, HostRuntime)


def test_runtime_factory_uv(tmp_path: Path):
    rt = RuntimeFactory.create(RuntimeType.UV, base_dir=tmp_path)
    assert isinstance(rt, HostRuntime)
