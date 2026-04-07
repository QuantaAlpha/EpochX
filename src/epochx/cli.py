"""CLI entry point for EpochX benchmark runner."""

from __future__ import annotations

import json
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from epochx.adapters import get_adapter, list_adapters
from epochx.runner import BenchRunner

app = typer.Typer(name="epochx-bench", help="EpochX - AI Agent Benchmark Runner")

console = Console()

# Shared runner (lazy singleton)
_runner: BenchRunner | None = None


def _get_runner() -> BenchRunner:
    global _runner
    if _runner is None:
        _runner = BenchRunner()
    return _runner


def _output(data: dict, as_json: bool) -> None:
    """Print data as JSON or human-readable text."""
    if as_json:
        console.print_json(json.dumps(data))
    else:
        for key, value in data.items():
            console.print(f"[bold]{key}:[/bold] {value}")


# ------------------------------------------------------------------
# bench list
# ------------------------------------------------------------------

@app.command("list")
def bench_list(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """List available benchmarks."""
    infos = list_adapters()
    if json_output:
        console.print_json(json.dumps(infos))
        return

    table = Table(title="Available Benchmarks")
    table.add_column("Name", style="cyan")
    table.add_column("Display Name", style="green")
    table.add_column("Description")
    table.add_column("Runtime", style="yellow")
    table.add_column("Profile", style="magenta")

    for info in infos:
        table.add_row(
            info["name"],
            info["display_name"],
            info["description"],
            info["agent_runtime"],
            info["resource_profile"],
        )
    console.print(table)


# ------------------------------------------------------------------
# bench info
# ------------------------------------------------------------------

@app.command("info")
def bench_info(
    benchmark: str = typer.Argument(help="Benchmark name"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Show benchmark details."""
    try:
        adapter = get_adapter(benchmark)
    except KeyError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)

    info = adapter.info()
    _output(info, json_output)


# ------------------------------------------------------------------
# bench run
# ------------------------------------------------------------------

@app.command("run")
def bench_run(
    benchmark: str = typer.Argument(help="Benchmark name"),
    task: Optional[str] = typer.Option(None, "--task", help="Task ID"),
    index: Optional[int] = typer.Option(None, "--index", help="Task index"),
    agent: Optional[str] = typer.Option(None, "--agent", help="Agent for full-auto mode"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Start a task environment."""
    if agent is not None:
        console.print("[red]Full-auto mode not yet implemented[/red]")
        raise typer.Exit(code=1)

    runner = _get_runner()
    result = runner.run_task(benchmark, task_id=task, task_index=index)

    if result.get("status") == "error":
        console.print(f"[red]Error:[/red] {result['message']}")
        raise typer.Exit(code=1)

    _output(result, json_output)


# ------------------------------------------------------------------
# bench collect
# ------------------------------------------------------------------

@app.command("collect")
def bench_collect(
    task_id: str = typer.Argument(help="Task ID"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Collect agent output."""
    runner = _get_runner()
    result = runner.collect_task(task_id)

    if result.get("status") == "error":
        console.print(f"[red]Error:[/red] {result['message']}")
        raise typer.Exit(code=1)

    _output(result, json_output)


# ------------------------------------------------------------------
# bench grade
# ------------------------------------------------------------------

@app.command("grade")
def bench_grade(
    task_id: str = typer.Argument(help="Task ID"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Evaluate collected output."""
    runner = _get_runner()
    result = runner.grade_task(task_id)

    if result.get("status") == "error":
        console.print(f"[red]Error:[/red] {result['message']}")
        raise typer.Exit(code=1)

    _output(result, json_output)


# ------------------------------------------------------------------
# bench stop
# ------------------------------------------------------------------

@app.command("stop")
def bench_stop(
    task_id: str = typer.Argument(help="Task ID"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Stop and clean up a task environment."""
    runner = _get_runner()
    result = runner.stop_task(task_id)

    if result.get("status") == "error":
        console.print(f"[red]Error:[/red] {result['message']}")
        raise typer.Exit(code=1)

    _output(result, json_output)


# ------------------------------------------------------------------
# bench next
# ------------------------------------------------------------------

@app.command("next")
def bench_next(
    benchmark: str = typer.Argument(help="Benchmark name"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Get next pending task."""
    runner = _get_runner()
    result = runner.get_next_task(benchmark)
    _output(result, json_output)


# ------------------------------------------------------------------
# bench status
# ------------------------------------------------------------------

@app.command("status")
def bench_status(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Show running environments."""
    runner = _get_runner()
    envs = runner.state.list_environments()

    if json_output:
        from dataclasses import asdict

        data = [asdict(e) for e in envs]
        console.print_json(json.dumps(data))
        return

    if not envs:
        console.print("No running environments.")
        return

    table = Table(title="Task Environments")
    table.add_column("Task ID", style="cyan")
    table.add_column("Benchmark", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Runtime")
    table.add_column("Started")

    for env in envs:
        table.add_row(
            env.task_id,
            env.benchmark,
            env.status,
            env.runtime,
            env.started_at,
        )
    console.print(table)


# ------------------------------------------------------------------
# bench tasks
# ------------------------------------------------------------------

@app.command("tasks")
def bench_tasks(
    benchmark: str = typer.Argument(help="Benchmark name"),
    limit: int = typer.Option(20, "--limit", help="Max tasks to show"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """List tasks for a benchmark."""
    try:
        adapter = get_adapter(benchmark)
    except KeyError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)

    tasks = adapter.fetch_tasks(limit=limit)

    if json_output:
        data = [
            {
                "id": t.id,
                "benchmark": t.benchmark,
                "external_id": t.external_id,
                "output_type": t.output_spec.type.value,
            }
            for t in tasks
        ]
        console.print_json(json.dumps(data))
        return

    table = Table(title=f"Tasks: {benchmark}")
    table.add_column("ID", style="cyan")
    table.add_column("External ID")
    table.add_column("Output Type", style="yellow")

    for t in tasks:
        table.add_row(t.id, t.external_id, t.output_spec.type.value)
    console.print(table)


# ------------------------------------------------------------------
# bench report
# ------------------------------------------------------------------

@app.command("report")
def bench_report(
    benchmark: Optional[str] = typer.Option(None, "--benchmark", "-b", help="Filter by benchmark"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Show aggregated results summary."""
    from epochx.exporter import Reporter

    reporter = Reporter(_get_runner().state)
    stats_list = reporter.get_stats(benchmark)

    if not stats_list:
        console.print("No results yet.")
        return

    if json_output:
        data = [s.to_dict() for s in stats_list]
        total_completed = sum(s.completed for s in stats_list)
        total_passed = sum(s.passed for s in stats_list)
        overall = {
            "total_completed": total_completed,
            "total_passed": total_passed,
            "overall_pass_rate": f"{total_passed / total_completed:.1%}" if total_completed else "N/A",
        }
        console.print_json(json.dumps({"benchmarks": data, "overall": overall}))
        return

    table = Table(title="Benchmark Results")
    table.add_column("Benchmark", style="cyan")
    table.add_column("Pass Rate", style="green", justify="right")
    table.add_column("Passed", justify="right")
    table.add_column("Failed", justify="right")
    table.add_column("Completed", justify="right")
    table.add_column("Total", justify="right")
    table.add_column("Progress", style="yellow")

    total_completed = 0
    total_passed = 0
    total_failed = 0

    for s in stats_list:
        # Build progress bar
        if s.total_tasks > 0:
            ratio = s.completed / s.total_tasks
            filled = int(ratio * 20)
            bar = "█" * filled + "░" * (20 - filled)
            progress = f"{bar} {s.completed}/{s.total_tasks}"
        else:
            progress = f"{'█' * 20} {s.completed}/{s.completed}"

        pass_rate = f"{s.pass_rate:.1%}" if s.completed else "N/A"

        table.add_row(
            s.display_name,
            pass_rate,
            str(s.passed),
            str(s.failed),
            str(s.completed),
            str(s.total_tasks),
            progress,
        )
        total_completed += s.completed
        total_passed += s.passed
        total_failed += s.failed

    # Summary row
    table.add_section()
    overall_rate = f"{total_passed / total_completed:.1%}" if total_completed else "N/A"
    table.add_row(
        "[bold]Overall[/bold]",
        f"[bold]{overall_rate}[/bold]",
        f"[bold]{total_passed}[/bold]",
        f"[bold]{total_failed}[/bold]",
        f"[bold]{total_completed}[/bold]",
        "",
        "",
    )
    console.print(table)

    # Per-task details for each benchmark
    task_results = reporter.get_task_results(benchmark)
    if task_results:
        console.print()
        detail_table = Table(title="Task Details")
        detail_table.add_column("Task ID", style="cyan")
        detail_table.add_column("Result", justify="center")
        detail_table.add_column("Score", justify="right")

        for r in task_results:
            result_mark = "[green]✓ PASS[/green]" if r["passed"] else "[red]✗ FAIL[/red]"
            detail_table.add_row(
                r["task_id"],
                result_mark,
                f"{r['score']:.1f}",
            )
        console.print(detail_table)


# ------------------------------------------------------------------
# bench export
# ------------------------------------------------------------------

@app.command("export")
def bench_export(
    benchmark: Optional[str] = typer.Option(None, "--benchmark", "-b", help="Filter by benchmark"),
    run_id: Optional[str] = typer.Option(None, "--run-id", help="Custom run ID"),
    output_dir: Optional[str] = typer.Option(None, "--output-dir", "-o", help="Output directory"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Export results to a structured directory for submission."""
    from pathlib import Path as P

    from epochx.exporter import Exporter

    exporter = Exporter(state=_get_runner().state)

    result = exporter.export(
        benchmark=benchmark,
        run_id=run_id,
        output_dir=P(output_dir) if output_dir else None,
    )

    if result.get("status") == "empty":
        console.print(f"[yellow]{result['message']}[/yellow]")
        raise typer.Exit(code=1)

    if json_output:
        console.print_json(json.dumps(result))
        return

    console.print(f"[green]Exported![/green]")
    console.print(f"  Run ID:     {result['run_id']}")
    console.print(f"  Output dir: {result['output_dir']}")

    summary = result.get("summary", {})
    console.print(f"  Overall:    {summary.get('overall', {}).get('overall_pass_rate', 'N/A')}")

    console.print(f"\nFiles:")
    out_path = P(result["output_dir"])
    for f in sorted(out_path.rglob("*")):
        if f.is_file():
            rel = f.relative_to(out_path)
            console.print(f"  {rel}")


# ------------------------------------------------------------------
# bench clean
# ------------------------------------------------------------------

@app.command("clean")
def bench_clean(
    benchmark: Optional[str] = typer.Option(None, "--benchmark", "-b", help="Only clean images for this benchmark"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be removed without removing"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Clean up Docker images to free disk space."""
    try:
        import docker as docker_lib
    except ImportError:
        console.print("[red]Error:[/red] docker package not installed")
        raise typer.Exit(code=1)

    client = docker_lib.from_env()

    # Patterns for benchmark Docker images
    patterns = {
        "swebench-verified": "swebench/sweb.eval",
        "swebench-pro": "jefzda/sweap-images",
        "terminal-bench": "alexgshaw/",
        "cybench": "cybench/",
        "core-bench": "core-bench",
    }

    if benchmark:
        if benchmark not in patterns:
            console.print(f"[yellow]No Docker images associated with '{benchmark}'[/yellow]")
            return
        patterns = {benchmark: patterns[benchmark]}

    images_to_remove: list[dict] = []

    # Build accurate size lookup from client.df() — img.attrs["Size"] is
    # unreliable on Docker 25+ with the containerd image store.
    df_images = client.df().get("Images", [])
    size_by_id = {img["Id"]: img.get("Size", 0) for img in df_images}

    for img in client.images.list():
        tags = img.tags
        if not tags:
            continue
        tag = tags[0]
        for bname, pattern in patterns.items():
            if pattern in tag:
                size_bytes = size_by_id.get(img.id, img.attrs.get("Size", 0))
                size_mb = size_bytes / (1024 * 1024)
                images_to_remove.append({
                    "image": tag,
                    "benchmark": bname,
                    "size_mb": round(size_mb, 1),
                    "id": img.short_id,
                })
                break

    if not images_to_remove:
        msg = "No benchmark Docker images found."
        if json_output:
            console.print_json(json.dumps({"status": "clean", "message": msg, "removed": 0}))
        else:
            console.print(f"[green]{msg}[/green]")
        return

    total_mb = sum(i["size_mb"] for i in images_to_remove)

    # Aggregate by benchmark
    by_bench: dict[str, dict] = {}
    for img_info in images_to_remove:
        bname = img_info["benchmark"]
        entry = by_bench.setdefault(bname, {"count": 0, "size_mb": 0.0})
        entry["count"] += 1
        entry["size_mb"] += img_info["size_mb"]

    def _fmt_size(mb: float) -> str:
        return f"{mb:.0f} MB" if mb < 1024 else f"{mb / 1024:.1f} GB"

    if json_output and dry_run:
        console.print_json(json.dumps({
            "status": "dry_run",
            "benchmarks": {
                b: {"count": v["count"], "size_mb": round(v["size_mb"], 1)}
                for b, v in sorted(by_bench.items())
            },
            "total_images": len(images_to_remove),
            "total_mb": round(total_mb, 1),
        }))
        return

    # Display summary table (grouped by benchmark, not per-image)
    table = Table(title="Docker Images" + (" (dry run)" if dry_run else ""))
    table.add_column("Benchmark", style="cyan")
    table.add_column("Images", justify="right")
    table.add_column("Size", justify="right", style="yellow")

    for bname, info in sorted(by_bench.items()):
        table.add_row(bname, str(info["count"]), _fmt_size(info["size_mb"]))

    table.add_section()
    table.add_row("[bold]Total[/bold]", f"[bold]{len(images_to_remove)}[/bold]", f"[bold]{_fmt_size(total_mb)}[/bold]")
    console.print(table)

    if dry_run:
        console.print("\n[yellow]Dry run — no images removed. Remove --dry-run to delete.[/yellow]")
        return

    # Actually remove
    removed = 0
    errors = []
    for img_info in images_to_remove:
        try:
            client.images.remove(img_info["image"], force=True)
            removed += 1
        except Exception as e:
            errors.append({"image": img_info["image"], "error": str(e)})

    if json_output:
        console.print_json(json.dumps({
            "status": "cleaned",
            "removed": removed,
            "errors": errors,
            "freed_mb": round(total_mb, 1),
        }))
    else:
        console.print(f"\n[green]Removed {removed}/{len(images_to_remove)} images, freed ~{total_str}[/green]")
        if errors:
            for err in errors:
                console.print(f"  [red]Failed:[/red] {err['image']}: {err['error']}")


# ------------------------------------------------------------------
# bench submit-run
# ------------------------------------------------------------------

@app.command("submit-run")
def bench_submit_run(
    benchmark: Optional[str] = typer.Option(None, "--benchmark", "-b", help="Benchmark name (default: all)"),
    api_key: Optional[str] = typer.Option(None, "--api-key", help="EpochX API key (default: from config)"),
    api_url: str = typer.Option("https://epochx.cc", "--api-url", help="EpochX API base URL"),
    agent_model: Optional[str] = typer.Option(None, "--model", help="Agent model name (e.g. claude-sonnet-4-20250514)"),
    agent_version: Optional[str] = typer.Option(None, "--version", "-v", help="Agent version"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Submit benchmark results to EpochX Arena."""
    import urllib.request
    import urllib.error
    from pathlib import Path

    from epochx.exporter import Reporter

    # 1. Resolve API key
    config_path = Path.home() / ".epochx" / "config.json"
    if not api_key and config_path.exists():
        try:
            with open(config_path) as f:
                config = json.loads(f.read())
            api_key = config.get("api_key")
            if config.get("api_url"):
                api_url = config["api_url"]
        except Exception:
            pass

    if not api_key:
        console.print("[red]Error:[/red] No API key. Pass --api-key or set up ~/.epochx/config.json")
        raise typer.Exit(code=1)

    # 2. Gather stats from local state
    reporter = Reporter(_get_runner().state)
    stats_list = reporter.get_stats(benchmark)

    if not stats_list:
        console.print("[yellow]No benchmark results found locally.[/yellow]")
        raise typer.Exit(code=1)

    # 3. Submit each benchmark's results
    base = api_url.rstrip("/")
    url = f"{base}/api/v1/arena/runs"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    results = []
    for stats in stats_list:
        payload = {
            "benchmark_name": stats.benchmark,
            "total_instances": stats.total_tasks,
            "completed_count": stats.completed,
            "passed_count": stats.passed,
            "failed_count": stats.failed,
        }
        if agent_model:
            payload["agent_model"] = agent_model
        if agent_version:
            payload["agent_version"] = agent_version

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = json.loads(resp.read().decode())
                results.append({"benchmark": stats.display_name, "status": "ok", "run_id": body.get("run_id"), "pass_rate": body.get("pass_rate")})
        except urllib.error.HTTPError as e:
            err_body = e.read().decode() if e.fp else ""
            detail = f"HTTP {e.code}"
            if err_body.strip():
                detail += f": {err_body.strip()}"
            results.append({"benchmark": stats.display_name, "status": "error", "detail": detail})
        except Exception as e:
            results.append({"benchmark": stats.display_name, "status": "error", "detail": str(e)})

    # 4. Output
    if json_output:
        console.print_json(json.dumps(results))
        return

    for r in results:
        if r["status"] == "ok":
            console.print(f"[green]✓[/green] {r['benchmark']}: submitted (run_id={r['run_id']}, pass_rate={r['pass_rate']:.1%})")
        else:
            console.print(f"[red]✗[/red] {r['benchmark']}: {r['detail']}")

    ok_count = sum(1 for r in results if r["status"] == "ok")
    console.print(f"\n[bold]{ok_count}/{len(results)} submitted.[/bold]")
    if ok_count > 0:
        console.print(f"View leaderboard: {base}/arena")


# ------------------------------------------------------------------
# main
# ------------------------------------------------------------------

def main() -> None:
    app()
