# Terminal-Bench 2.0 — Benchmark Guide

> 89+ hard terminal tasks — coding, sysadmin, scientific computing, Docker-verified.

## Overview

| Item | Value |
|------|-------|
| **Name** | `terminal-bench` |
| **Runtime** | Docker |
| **Tasks** | 89 |
| **Output Type** | `SNAPSHOT_DIFF` (final container state is verified) |
| **Evaluation** | Automated test scripts inside container (`test.sh`) |
| **Resource Profile** | `medium` |
| **Docker Images** | Pre-built from DockerHub: `alexgshaw/{task-name}:{date}` |
| **Data Source** | Local repo: `benchmarks/terminal-bench/repo/` |

## Data Source

- Tasks loaded from `benchmarks/terminal-bench/repo/` (each subdirectory is a task)
- Each task contains: `task.toml` (metadata), `instruction.md` (task description), `tests/` (verification), `environment/Dockerfile`
- Docker images pulled from DockerHub (pre-built per task)

## Quick Start

```bash
# Start a specific task
epochx bench run terminal-bench --task chess-best-move --json

# Start by index
epochx bench run terminal-bench --index 0 --json

# Start first available
epochx bench run terminal-bench --json
```

## Workspace After Setup

```
{workspace}/
├── .epochx/
│   ├── meta.json
│   ├── prompt.md      # Contains: task instructions, difficulty, category
│   ├── tests/         # Verification scripts (copied from repo)
│   │   ├── test.sh
│   │   └── test_outputs.py
│   └── output.txt     # Written by `collect` (test results JSON)
```

**Inside the Docker container**:

```
/app/                    # 常见工作目录（取决于 Dockerfile 中的 WORKDIR）
├── (task-specific files: source code, data, configs)
└── ...
```

> **Important**: 每个任务有独立的 Docker 镜像，预装了任务所需的工具和数据。工作目录从 prompt.md 读取。

## How to Solve

1. **Read the prompt**: `cat {workspace}/.epochx/prompt.md`
   - Contains full task instructions, difficulty, and category
   - The instructions describe what you need to build/fix/configure

2. **SSH into the container**:
   ```bash
   ssh {ssh_host}
   cd {container_workdir}   # 路径来自 prompt.md
   ```

3. **Explore the environment**: See what's available
   ```bash
   ssh {ssh_host} 'ls -la /app/ && which python3 && which gcc'
   ```

4. **Complete the task**: Follow the instructions
   - Tasks vary widely: compile code, train models, configure servers, write scripts, etc.
   - All work happens inside the container
   - Internet access is available (install packages, download resources)

5. **Verify your work** (optional):
   ```bash
   # Check if expected output files exist
   ssh {ssh_host} 'ls -la /app/output* 2>/dev/null'
   ```

## Collect + Stop + Grade

```bash
# Collect runs test.sh inside the container (verifies final state)
epochx bench collect terminal-bench/{task_name}

# Stop removes the container
epochx bench stop terminal-bench/{task_name}

# Grade parses the test results
epochx bench grade terminal-bench/{task_name}
```

> **注意**: `collect` 会通过 SSH 在容器内运行验证脚本（test.sh），必须在 `stop` 之前执行。
> `grade` 解析已收集的测试结果，不需要容器运行。

## Task Categories

| Category | Examples |
|----------|---------|
| **Software Engineering** | Build projects, fix bugs, implement features |
| **Scientific Computing** | ML training, statistical sampling, data processing |
| **Systems Administration** | Server config, process management |
| **Games / Puzzles** | Chess analysis, game implementations |
| **Cybersecurity** | Hash cracking, vulnerability analysis |

## Task Difficulty

| Difficulty | Expert Time | Junior Time |
|-----------|-------------|-------------|
| **easy** | < 15 min | < 1 hour |
| **medium** | 15 min - 4 hours | 1 - 24 hours |
| **hard** | 4+ hours | 1+ days |

## Docker Image Details

- **Registry**: DockerHub
- **Naming**: `alexgshaw/{task-name}:{date}` (e.g., `alexgshaw/chess-best-move:20251031`)
- **Contents**: Pre-configured environment with task-specific tools, data, and dependencies
- **Auto-pull**: The `run` command automatically pulls the image if not present locally

## Verification System

Terminal-Bench uses **outcome-based verification**:
- test.sh runs inside the container after the agent finishes
- Tests check the **final container state** (files, outputs, configurations)
- Multiple valid solution paths are acceptable
- Results: reward = 1 (pass) or 0 (fail)
- Detailed test output available via CTRF JSON report

## Tips

- **Read instructions carefully**: Tasks are diverse and specific. The instruction.md contains everything you need.
- **Internet available**: You can `apt-get install`, `pip install`, download files, etc.
- **No specific output file needed**: Tests verify the container state (files at specific paths, running services, etc.)
- **Check test expectations**: Look at `{workspace}/.epochx/tests/test_outputs.py` to understand what's being verified
- **Timeouts**: Default agent timeout is 900s (15 min). Some tasks have custom timeouts.
