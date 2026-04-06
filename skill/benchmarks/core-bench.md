# CORE-Bench — Benchmark Guide

> 90 computational reproducibility tasks — Docker-in-Docker, vision+text grading.

## Overview

| Item | Value |
|------|-------|
| **Name** | `core-bench` |
| **Runtime** | Docker |
| **Tasks** | 90 |
| **Output Type** | `FILE_CONTENT` |
| **Output Location** | `results/` directory |
| **Evaluation** | Custom script (simplified: checks output existence) |
| **Resource Profile** | `heavy` |
| **Docker Image** | `core-bench:latest` |
| **Special** | Requires Docker-in-Docker (nested Docker) |

## Data Source

Tasks are loaded from directories in:
```
benchmarks/core-bench/repo/benchmark/dataset/{task_id}/
```

Each task directory contains:
```
{task_id}/
├── metadata.json     # Task metadata
├── README.md         # Task description (used in prompt)
└── (other files)     # Task-specific data files
```

## Quick Start

```bash
# Start a specific task
epochx bench run core-bench --task {task_id} --json

# Start first available
epochx bench run core-bench --json
```

## Workspace After Setup

```
{workspace}/
├── .epochx/
│   ├── meta.json
│   ├── prompt.md      # Contains: task ID, description from README, instructions
│   └── output.txt     # Written by `collect` (concatenated results/)
├── results/
│   └── (write your result files here)
├── metadata.json      # Copied from benchmark data
├── README.md          # Copied from benchmark data
└── (other task data)
```

**Inside the Docker container**:
- `core-bench:latest` image with Docker daemon available
- System dependency: `docker` (Docker-in-Docker)
- `/.epochx/` mounted from host workspace

## How to Solve

1. **Read the prompt**: `cat {workspace}/.epochx/prompt.md`
   - Contains the computational reproducibility task description
   - References the task README and metadata

2. **SSH into the container**:
   ```bash
   ssh {ssh_host}
   ```

3. **Read task details**:
   ```bash
   ssh {ssh_host} 'cat /.epochx/../metadata.json'
   ssh {ssh_host} 'cat /.epochx/../README.md'
   ```

4. **Reproduce the computation**:
   - Follow the instructions in README.md
   - May involve running scripts, building sub-containers, processing data
   - Docker-in-Docker is available if needed

5. **Write results** to the `results/` directory:
   ```bash
   ssh {ssh_host} 'mkdir -p /.epochx/../results'
   ssh {ssh_host} 'echo "result data" > /.epochx/../results/output.txt'
   ```
   Or locally:
   ```bash
   mkdir -p {workspace}/results
   echo "result data" > {workspace}/results/output.txt
   ```

## Collect + Grade + Stop

```bash
# Collect concatenates ALL files in results/ with separators
epochx bench collect core-bench/{task_id}

epochx bench grade core-bench/{task_id}
epochx bench stop core-bench/{task_id}
```

## Output Collection

The `collect` command reads **all files** in `{workspace}/results/` recursively:
- Each file is included with a separator: `--- relative/path ---`
- Binary files are noted as `<binary file: name>`
- Files are sorted alphabetically

## Docker Image

- **Image**: `core-bench:latest`
- **Must be built locally**: `cd benchmarks/core-bench/repo && docker build -t core-bench:latest .`
- **Auto-pull attempted** if not found locally
- **Resource-heavy**: May need significant CPU, memory, and disk

## Tips

- **Docker-in-Docker**: The container may need to run its own Docker containers. Ensure the Docker socket is accessible.
- **Long-running tasks**: Timeout is 3600 seconds (1 hour). Complex reproductions may take significant time.
- **Check metadata.json** for additional task parameters and expected outputs
- **Binary outputs**: If the task produces images or binary data, place them in `results/` — they'll be noted during collection
- **Heavy resources**: This benchmark has `heavy` resource profile — ensure sufficient CPU, memory, and disk space
