"""Export and report benchmark results."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from epochx.adapters import get_adapter, list_adapters
from epochx.core.state import StateManager


@dataclass
class BenchmarkStats:
    """Aggregated statistics for one benchmark."""

    benchmark: str
    display_name: str
    total_tasks: int
    completed: int
    passed: int
    failed: int
    pending: int
    pass_rate: float  # 0.0–1.0, among completed only

    def to_dict(self) -> dict:
        return {
            "benchmark": self.benchmark,
            "display_name": self.display_name,
            "total_tasks": self.total_tasks,
            "completed": self.completed,
            "passed": self.passed,
            "failed": self.failed,
            "pending": self.pending,
            "pass_rate": f"{self.pass_rate:.1%}" if self.completed else "N/A",
        }


class Reporter:
    """Generate benchmark result reports from state."""

    def __init__(self, state: StateManager | None = None):
        self.state = state or StateManager()

    def get_stats(self, benchmark: str | None = None) -> list[BenchmarkStats]:
        """Compute stats for each benchmark (or a specific one)."""
        results = self.state.get_results()

        # Group results by benchmark
        by_benchmark: dict[str, list[dict]] = {}
        for _tid, r in results.items():
            bname = r.get("benchmark", "unknown")
            by_benchmark.setdefault(bname, []).append(r)

        # Determine which benchmarks to report
        if benchmark:
            benchmarks_to_report = [benchmark]
        else:
            # All benchmarks that have at least one result
            benchmarks_to_report = sorted(by_benchmark.keys())

        stats: list[BenchmarkStats] = []
        for bname in benchmarks_to_report:
            # Get total tasks count from adapter
            try:
                adapter = get_adapter(bname)
                total = len(adapter.fetch_tasks())
                display_name = adapter.display_name
            except (KeyError, Exception):
                total = 0
                display_name = bname

            bench_results = by_benchmark.get(bname, [])
            completed = len(bench_results)
            passed = sum(1 for r in bench_results if r.get("passed"))
            failed = completed - passed

            stats.append(
                BenchmarkStats(
                    benchmark=bname,
                    display_name=display_name,
                    total_tasks=total,
                    completed=completed,
                    passed=passed,
                    failed=failed,
                    pending=max(0, total - completed),
                    pass_rate=passed / completed if completed else 0.0,
                )
            )

        return stats

    def get_task_results(self, benchmark: str | None = None) -> list[dict]:
        """Get per-task results, optionally filtered by benchmark."""
        results = self.state.get_results(benchmark=benchmark)
        out = []
        for task_id, r in sorted(results.items()):
            item = {
                "task_id": task_id,
                "benchmark": r.get("benchmark", ""),
                "passed": r.get("passed", False),
                "score": r.get("score", 0.0),
                "details": r.get("details", {}),
            }
            if r.get("trajectory"):
                item["trajectory"] = r["trajectory"]
            if r.get("output"):
                item["output"] = r["output"]
            out.append(item)
        return out


class Exporter:
    """Export results to a structured directory."""

    def __init__(
        self,
        state: StateManager | None = None,
        base_dir: Path | None = None,
    ):
        self.state = state or StateManager()
        self.base_dir = base_dir or (Path.home() / ".epochx" / "exports")
        self.reporter = Reporter(self.state)

    @property
    def arena_dir(self) -> Path:
        """Get arena dir from current run."""
        return self.state.get_arena_dir()

    def export(
        self,
        benchmark: str | None = None,
        run_id: str | None = None,
        output_dir: Path | None = None,
    ) -> dict:
        """Export results to a structured directory.

        Returns a summary dict with export metadata.
        """
        # Determine run_id and output directory
        if run_id is None:
            ts = datetime.now().strftime("%Y%m%d-%H%M%S")
            if benchmark:
                run_id = f"{benchmark}-{ts}"
            else:
                run_id = f"all-{ts}"

        if output_dir is None:
            output_dir = self.base_dir / run_id

        output_dir.mkdir(parents=True, exist_ok=True)

        # Collect stats and results
        stats_list = self.reporter.get_stats(benchmark)
        task_results = self.reporter.get_task_results(benchmark)

        if not task_results:
            return {
                "status": "empty",
                "message": "No results to export.",
                "run_id": run_id,
            }

        # 1. Write results.jsonl (all task results)
        results_path = output_dir / "results.jsonl"
        with open(results_path, "w") as f:
            for r in task_results:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

        # 2. Write predictions.jsonl (per-benchmark submission format)
        by_bench_dir = output_dir / "by_benchmark"
        benchmarks_exported = set()
        for r in task_results:
            bname = r["benchmark"]
            benchmarks_exported.add(bname)

        for bname in benchmarks_exported:
            bench_dir = by_bench_dir / bname
            bench_dir.mkdir(parents=True, exist_ok=True)

            # Write per-benchmark results.jsonl
            bench_results = [r for r in task_results if r["benchmark"] == bname]
            with open(bench_dir / "results.jsonl", "w") as f:
                for r in bench_results:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")

            # Write per-benchmark predictions.jsonl (submission format)
            predictions = self._build_predictions(bname, bench_results)
            if predictions:
                with open(bench_dir / "predictions.jsonl", "w") as f:
                    for p in predictions:
                        f.write(json.dumps(p, ensure_ascii=False) + "\n")

        # 3. Write summary.json
        summary = self._build_summary(run_id, stats_list, task_results)
        summary_path = output_dir / "summary.json"
        summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False))

        # 4. Update 'latest' symlink
        latest_link = self.base_dir / "latest"
        if latest_link.is_symlink() or latest_link.exists():
            latest_link.unlink()
        try:
            latest_link.symlink_to(output_dir)
        except OSError:
            pass  # Windows or permission issues

        return {
            "status": "exported",
            "run_id": run_id,
            "output_dir": str(output_dir),
            "summary": summary,
        }

    def _build_summary(
        self, run_id: str, stats_list: list[BenchmarkStats], task_results: list[dict]
    ) -> dict:
        """Build summary.json content."""
        total_completed = sum(s.completed for s in stats_list)
        total_passed = sum(s.passed for s in stats_list)

        return {
            "run_id": run_id,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "benchmarks": {
                s.benchmark: s.to_dict() for s in stats_list
            },
            "overall": {
                "total_completed": total_completed,
                "total_passed": total_passed,
                "total_failed": total_completed - total_passed,
                "overall_pass_rate": (
                    f"{total_passed / total_completed:.1%}"
                    if total_completed
                    else "N/A"
                ),
            },
        }

    def _build_predictions(self, benchmark: str, results: list[dict]) -> list[dict]:
        """Build leaderboard-format predictions for a benchmark.

        Reads the actual agent output (patch/answer) from workspace files.
        """
        predictions = []

        for r in results:
            task_id = r["task_id"]
            # Extract external_id from task_id (e.g., "swebench-verified/django__django-13128" -> "django__django-13128")
            external_id = task_id.split("/", 1)[-1] if "/" in task_id else task_id

            # Read the agent output from workspace
            workspace = self.arena_dir / benchmark / external_id
            output_path = workspace / ".epochx" / "output.txt"
            output = ""
            if output_path.exists():
                output = output_path.read_text()

            if benchmark in ("swebench-verified", "swebench-pro"):
                # SWE-bench standard submission format
                predictions.append({
                    "instance_id": external_id,
                    "model_name_or_path": "epochx-agent",
                    "model_patch": output,
                })
            elif benchmark == "terminal-bench":
                # Terminal-Bench: task name + reward
                predictions.append({
                    "task_id": external_id,
                    "reward": r.get("details", {}).get("reward", 0),
                    "passed": r.get("passed", False),
                })
            elif benchmark == "dabstep":
                predictions.append({
                    "task_id": external_id,
                    "answer": output,
                    "passed": r.get("passed", False),
                })
            elif benchmark == "tau-bench":
                predictions.append({
                    "task_id": external_id,
                    "passed": r.get("passed", False),
                    "score": r.get("score", 0.0),
                })
            else:
                # Generic format
                predictions.append({
                    "task_id": external_id,
                    "output": output[:1000] if output else "",
                    "passed": r.get("passed", False),
                    "score": r.get("score", 0.0),
                })

        return predictions
