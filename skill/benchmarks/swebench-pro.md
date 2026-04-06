# SWE-bench Pro — Benchmark Guide

> 731 real GitHub issues — generate code patches, evaluated via Docker tests.

## Overview

| Item | Value |
|------|-------|
| **Name** | `swebench-pro` |
| **Runtime** | Docker |
| **Tasks** | 731 |
| **Output Type** | `GIT_DIFF` |
| **Evaluation** | Docker test suite (via ScaleAI eval scripts) |
| **Resource Profile** | `medium` |
| **Docker Images** | Pre-built from DockerHub: `jefzda/sweap-images:{tag}` |
| **Dataset** | HuggingFace: `ScaleAI/SWE-bench_Pro` |

## Data Source

- Tasks loaded from HuggingFace dataset `ScaleAI/SWE-bench_Pro` (requires `datasets` library)
- Docker images pulled from DockerHub (`jefzda/sweap-images`)
- Evaluation scripts in `benchmarks/swebench-pro/repo-pro/` (ScaleAI's SWE-bench_Pro-os)
- Run scripts per instance in `benchmarks/swebench-pro/repo-pro/run_scripts/`

## Quick Start

```bash
# Start a specific task (image is pulled automatically, may take a few minutes)
epochx bench run swebench-pro --task django__django-16379 --json

# Start first available
epochx bench run swebench-pro --json
```

## Workspace After Setup

```
{workspace}/
├── .epochx/
│   ├── meta.json
│   ├── prompt.md      # Contains: repo name, base commit, full issue description
│   └── output.txt     # Written by `collect` (git diff)
```

**Inside the Docker container** (the actual working environment):

```
{container_workdir}/     # 自动检测，写入 prompt.md（常见: /app, /testbed）
├── (full repo contents)
└── .git/
```

> **Important**: The repo lives **inside the container**, not on the host. All code editing happens via SSH。
> **工作目录自动检测**: prompt.md 的 `Working directory inside container` 字段会标注实际路径，不需要手动探测。

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
   ```bash
   ssh {ssh_host} 'cat > /tmp/patch.py << "PYEOF"
   import re
   # ... your fix logic ...
   PYEOF
   python3 /tmp/patch.py'
   ```

   Or use `sed` / heredoc for targeted edits:
   ```bash
   ssh {ssh_host} "cd {container_workdir} && sed -i 's/old_code/new_code/' path/to/file.py"
   ```

5. **Verify your fix** (optional but recommended):
   ```bash
   ssh {ssh_host} 'cd {container_workdir} && python -m pytest tests/test_relevant.py -x -q 2>&1 | tail -20'
   ```

6. **Commit or just leave changes** (both work):
   ```bash
   # collect 会自动与 base_commit 对比，无论是否 commit
   ssh {ssh_host} 'cd {container_workdir} && git add -A && git commit -m "fix: resolve the issue"'
   # 或不 commit，collect 也能正确提取 diff
   ```

## Collect + Stop + Grade

```bash
# Collect captures `git diff {base_commit}` from inside the container
epochx bench collect swebench-pro/django__django-16379

# Stop removes the agent's container (释放资源)
epochx bench stop swebench-pro/django__django-16379

# Grade launches a fresh container, applies patch, runs test suite
epochx bench grade swebench-pro/django__django-16379
```

> **注意顺序**: 先 `collect`（从 agent 容器取 diff）→ 再 `stop`（关 agent 容器）→ 最后 `grade`（启动评测专用容器）。

## Docker Image Details

- **Registry**: DockerHub (`jefzda/sweap-images`)
- **Tag format**: `{org}.{repo}-{instance_hash}` (computed by ScaleAI's `helper_code/image_uri.py`)
- **Contents**: Full repo pre-checked out at the correct base commit, with dependencies installed
- **Auto-pull**: The `run` command automatically pulls the image if not present locally

Example image: `jefzda/sweap-images:django.django-16379`

## Task Metadata

Each task includes:
- `repo`: GitHub repo (e.g., `django/django`)
- `dockerhub_tag`: Tag string for Docker image lookup
- `before_repo_set_cmd`: Commands to run before repo setup (if any)
- `selected_test_files`: Test files to run for evaluation
- `fail_to_pass`: Tests that should change from FAIL to PASS
- `pass_to_pass`: Tests that should remain passing

## Evaluation Scripts

ScaleAI provides evaluation infrastructure at:
```
benchmarks/swebench-pro/repo-pro/
├── swe_bench_pro_eval.py          # Main eval script (--use_local_docker)
├── run_scripts/
│   └── instance_{id}/
│       └── run_script.sh          # Per-instance test runner
├── helper_code/
│   └── image_uri.py               # Docker image URI computation
└── dockerfiles/                    # Dockerfile templates
```

## Tips

- **Don't overwrite container contents**: The host workspace `.epochx/` is mounted at `/.epochx` inside the container. Everything else is the container's own filesystem.
- **Use `git diff` to verify** before collecting: `ssh {ssh_host} 'cd {container_workdir} && git diff'`
- **Pre-installed deps**: The Docker images come with all project dependencies pre-installed
- **Large images**: First pull can be slow (1-5 GB per image). Subsequent tasks for the same repo reuse cached layers.
- **Repo location自动检测**: prompt.md 中会标注实际路径，不需要手动探测。
- **Test before committing**: Run the relevant test files to verify your fix doesn't break anything
