"""Tests for PortManager."""

from pathlib import Path

from epochx.core.port_manager import PortManager


def test_allocate_returns_port_in_range(tmp_path: Path):
    pm = PortManager(state_file=tmp_path / "ports.json")
    port = pm.allocate("task-1")
    assert PortManager.BASE_PORT <= port <= PortManager.MAX_PORT


def test_allocate_unique_ports(tmp_path: Path):
    pm = PortManager(state_file=tmp_path / "ports.json")
    port1 = pm.allocate("task-1")
    port2 = pm.allocate("task-2")
    assert port1 != port2


def test_allocate_returns_same_port_for_same_task(tmp_path: Path):
    pm = PortManager(state_file=tmp_path / "ports.json")
    port1 = pm.allocate("task-1")
    port2 = pm.allocate("task-1")
    assert port1 == port2


def test_release_frees_port(tmp_path: Path):
    pm = PortManager(state_file=tmp_path / "ports.json")
    port1 = pm.allocate("task-1")
    pm.release("task-1")
    assert pm.get_port("task-1") is None
    # After release, the same port can be re-allocated
    port2 = pm.allocate("task-2")
    assert port2 == port1


def test_state_persists_across_instances(tmp_path: Path):
    state_file = tmp_path / "ports.json"
    pm1 = PortManager(state_file=state_file)
    port = pm1.allocate("task-1")

    pm2 = PortManager(state_file=state_file)
    assert pm2.get_port("task-1") == port
