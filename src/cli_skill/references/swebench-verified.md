# SWE-bench Verified — Benchmark Guide

> 500 human-validated GitHub issues — generate code patches, evaluated via standard swebench harness.

## Overview

| Item | Value |
|------|-------|
| **Name** | `swebench-verified` |
| **Runtime** | Docker |
| **Tasks** | 500 |
| **Output Type** | `GIT_DIFF` |
| **Evaluation** | Docker test suite (via standard `swebench` harness) |
| **Resource Profile** | `medium` |
| **Docker Images** | Pre-built from DockerHub: `swebench/sweb.eval.x86_64.{id}:latest` |
| **Dataset** | HuggingFace: `princeton-nlp/SWE-bench_Verified` |

## Data Source

- Tasks loaded from HuggingFace dataset `princeton-nlp/SWE-bench_Verified` (requires `datasets` library)
- Docker images pulled from DockerHub (`swebench/` namespace)
- Evaluation via `python -m swebench.harness.run_evaluation` (requires `swebench` pip package)

## Quick Start

```bash
# Install dependencies
uv pip install -e ".[swebench]"

# Start a specific task (image is pulled automatically)
epochx bench run swebench-verified --task django__django-10097 --json

# Start first available
epochx bench run swebench-verified --json
```

## Workspace After Setup

```
{workspace}/
├── .epochx/
│   ├── meta.json
│   ├── prompt.md      # Contains: repo name, base commit, full issue description
│   └── output.txt     # Written by `collect` (git diff)
```

**Inside the Docker container**:

```
/testbed/                # 默认工作目录（自动检测，写入 prompt.md）
├── (full repo contents)
└── .git/
```

> **Important**: The repo lives **inside the container**, not on the host. All code editing happens via SSH.

## How to Solve

1. **Read the prompt**: `cat {workspace}/.epochx/prompt.md`
   - Contains the GitHub issue (problem_statement)
   - Specifies the repo name, base commit, and **container working directory**

2. **SSH into the container**:
   ```bash
   ssh {ssh_host}
   cd {container_workdir}   # 路径来自 prompt.md
   ```

3. **Understand the issue**: Read relevant source files
   ```bash
   ssh {ssh_host} 'cd {container_workdir} && find . -name "*.py" | head -20'
   ssh {ssh_host} 'cd {container_workdir} && git log --oneline -5'
   ```

4. **Make code changes**: Edit files to fix the issue

5. **Verify your fix** (optional but recommended):
   ```bash
   ssh {ssh_host} 'cd {container_workdir} && python -m pytest tests/test_relevant.py -x -q 2>&1 | tail -20'
   ```

6. **Commit or just leave changes** (both work):
   ```bash
   # collect 会自动与 base_commit 对比，无论是否 commit
   ssh {ssh_host} 'cd {container_workdir} && git add -A && git commit -m "fix: resolve the issue"'
   ```

## Collect + Stop + Grade

```bash
# Collect captures `git diff {base_commit}` from inside the container
epochx bench collect swebench-verified/{instance_id}

# Stop removes the agent's container
epochx bench stop swebench-verified/{instance_id}

# Grade launches the standard swebench harness (fresh container, apply patch, run tests)
epochx bench grade swebench-verified/{instance_id}
```

> **注意顺序**: 先 `collect`（从 agent 容器取 diff）→ 再 `stop`（关 agent 容器）→ 最后 `grade`（swebench harness 启动评测容器）。

## vs SWE-bench Pro

| | SWE-bench Verified | SWE-bench Pro |
|---|---|---|
| **Tasks** | 500 (12 Python repos) | 731 (41 repos, multi-language) |
| **Curation** | Human-validated by professional SWEs | Scale AI curated |
| **Docker Images** | `swebench/` namespace | `jefzda/sweap-images` |
| **Eval Harness** | Standard `swebench` pip package | ScaleAI custom `swe_bench_pro_eval.py` |
| **Difficulty** | Has `difficulty` field (4 levels) | Generally harder (avg 107 lines change) |

## Docker Image Details

- **Registry**: DockerHub (`swebench/` namespace)
- **Naming**: `swebench/sweb.eval.x86_64.{owner}_{build_id}_{repo}-{number}:latest`
- **Example**: `swebench/sweb.eval.x86_64.django_1776_django-10097:latest`
- **Contents**: Full repo pre-checked out at the correct base commit, with dependencies installed
- **Auto-pull**: The `run` command automatically pulls the image if not present locally

## Task Metadata

Each task includes:
- `repo`: GitHub repo (e.g., `django/django`)
- `base_commit`: The commit to diff against
- `version`: Python version string
- `difficulty`: Task difficulty level
- `FAIL_TO_PASS`: Tests that should change from FAIL to PASS
- `PASS_TO_PASS`: Tests that should remain passing

## Tips

- **Same workflow as swebench-pro**: SSH in, edit code, collect diff
- **Pre-installed deps**: Docker images come with all project dependencies pre-installed
- **Large images**: First pull can be slow (1-5 GB). Subsequent tasks for the same repo reuse cached layers.
- **Test before committing**: Run relevant test files to verify your fix
- **Use `git diff` to verify**: `ssh {ssh_host} 'cd {container_workdir} && git diff'`
