# DA-Code — Benchmark Guide

> Data science agent tasks — insight, manipulation, ML, statistics, visualization.

## Overview

| Item | Value |
|------|-------|
| **Name** | `da-code` |
| **Runtime** | Docker |
| **Tasks** | Varies (loaded from JSON task definitions) |
| **Output Type** | `FILE_CONTENT` |
| **Output File** | Specified per task (default: `output.txt`) |
| **Evaluation** | Custom script (simplified: checks output existence) |
| **Resource Profile** | `medium` |
| **Docker Image** | `da_agent-image` |

## Data Source

Tasks are loaded from JSON files in:
```
benchmarks/da-code/repo/da_code/source/*.json
```

Each JSON file may contain a single object or a list of task objects.

## Quick Start

```bash
# Start a specific task
epochx bench run da-code --task {task_id} --json

# Start first available
epochx bench run da-code --json
```

## Workspace After Setup

```
{workspace}/
├── .epochx/
│   ├── meta.json
│   ├── prompt.md      # Contains: question, category, data file list, output file name
│   └── output.txt     # Written by `collect`
└── (data files if any)
```

**Inside the Docker container**:
- `da_agent-image` provides a Python data science environment
- `/.epochx/` is mounted from the host workspace

## How to Solve

1. **Read the prompt**: `cat {workspace}/.epochx/prompt.md`
   - Contains the data science question
   - Specifies category (insight, manipulation, ML, stats, visualization)
   - Lists data files and output file name

2. **SSH into the container**:
   ```bash
   ssh {ssh_host}
   ```

3. **Locate data files**: Check the prompt for `data_files` list
   ```bash
   ssh {ssh_host} 'ls /.epochx/'
   ssh {ssh_host} 'find / -name "*.csv" -o -name "*.json" 2>/dev/null | head -20'
   ```

4. **Write and run analysis code**:
   ```bash
   ssh {ssh_host} 'python3 << "PYEOF"
   import pandas as pd
   # Your analysis here
   result = "analysis output"
   with open("/.epochx/output.txt", "w") as f:
       f.write(result)
   PYEOF'
   ```

5. **Write output** to the specified file:
   - Check `prompt.md` for the exact output filename
   - Default is `output.txt`
   - Write via the `/.epochx` mount or directly in the container

## Collect + Grade + Stop

```bash
epochx bench collect da-code/{task_id}
epochx bench grade da-code/{task_id}
epochx bench stop da-code/{task_id}
```

## Task Categories

| Category | Description |
|----------|-------------|
| `insight` | Derive insights from data |
| `manipulation` | Transform/clean data |
| `ml` | Machine learning tasks |
| `statistics` | Statistical analysis |
| `visualization` | Create charts/plots |

## Task Metadata

Each task includes:
- `category`: One of the categories above
- `difficulty`: Difficulty level

## Docker Image

- **Image**: `da_agent-image`
- **Must be built locally** if not available: `cd benchmarks/da-code/repo && docker build -t da_agent-image .`
- **Auto-pull attempted** if not found locally

## Tips

- **Check the output file name** in the prompt — it varies per task (not always `output.txt`)
- **Data files may be inside the container** or referenced by path in the prompt
- **Python scientific stack** is typically available: pandas, numpy, matplotlib, scikit-learn
- **Write the output file correctly** — the collect command reads from `{workspace}/{output_file}`
