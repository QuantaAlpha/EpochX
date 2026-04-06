"""Tests for the CLI entry point."""

from __future__ import annotations

import json

from typer.testing import CliRunner

from epochx.cli import app

runner = CliRunner()


def test_bench_list():
    """bench list exits 0 and output contains 'dabstep'."""
    result = runner.invoke(app, ["bench", "list"])
    assert result.exit_code == 0
    assert "dabstep" in result.output


def test_bench_list_json():
    """bench list --json exits 0 and returns valid JSON with dabstep entry."""
    result = runner.invoke(app, ["bench", "list", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    names = [d["name"] for d in data]
    assert "dabstep" in names
