# Cybench — Benchmark Guide

> 40 CTF security challenges — crypto/forensics/pwn/reversing/web.

## Overview

| Item | Value |
|------|-------|
| **Name** | `cybench` |
| **Runtime** | Docker |
| **Tasks** | 40+ |
| **Output Type** | `ANSWER_STRING` (the flag) |
| **Answer File** | `.epochx/answer.txt` |
| **Evaluation** | Exact string match of the flag |
| **Resource Profile** | `medium` |
| **Docker Image** | `cybench/cybench:latest` |

## Data Source

Tasks are scanned from:
```
benchmarks/cybench/repo/benchmark/{source}/{challenge}/metadata/metadata.json
```

Where `{source}` is the CTF origin (e.g., `hackthebox`, `project-sekai-ctf`).

## Quick Start

```bash
# Start a specific challenge
epochx bench run cybench --task {challenge_name} --json

# Start first available
epochx bench run cybench --json
```

## Workspace After Setup

```
{workspace}/
├── .epochx/
│   ├── meta.json
│   ├── prompt.md      # Contains: challenge description (hard_prompt or easy_prompt)
│   └── answer.txt     # ← WRITE THE FLAG HERE
└── challenge/
    ├── (challenge-specific files copied from benchmark data)
    └── ...
```

**Inside the Docker container**:
- The `cybench/cybench:latest` image comes with security tools pre-installed
- `/.epochx/` is mounted from the host workspace
- Challenge files are copied to `{workspace}/challenge/` on the host

## How to Solve

1. **Read the prompt**: `cat {workspace}/.epochx/prompt.md`
   - Contains the CTF challenge description
   - Categories: crypto, forensics, pwn, reversing, web

2. **SSH into the container**:
   ```bash
   ssh {ssh_host}
   ```

3. **Access challenge files** (available at `/.epochx/../challenge/` or copy them in):
   ```bash
   # Challenge files are in the host workspace, copy via /.epochx mount if needed
   ssh {ssh_host} 'ls /.epochx/'

   # Or use scp to bring challenge files into the container
   scp -r {workspace}/challenge/ {ssh_host}:/tmp/challenge/
   ```

4. **Use available tools** inside the container:
   ```bash
   ssh {ssh_host} 'which python3 gdb strings file binwalk'
   ```

5. **Find the flag**: Analyze the challenge and extract the flag

6. **Submit the flag** — write to answer.txt:
   ```bash
   # Via the mounted volume
   ssh {ssh_host} 'echo "flag{found_it_123}" > /.epochx/answer.txt'

   # OR directly on the host
   echo "flag{found_it_123}" > {workspace}/.epochx/answer.txt
   ```

## Collect + Grade + Stop

```bash
epochx bench collect cybench/{challenge_name}
epochx bench grade cybench/{challenge_name}     # → exact match against known flag
epochx bench stop cybench/{challenge_name}
```

## Task Metadata

Each task includes:
- `source`: CTF origin (e.g., `hackthebox`)
- `difficulty`: Challenge difficulty rating
- `categories`: List of categories (e.g., `["crypto"]`, `["web", "forensics"]`)
- `task_dir`: Path to the challenge files on disk

## Challenge Structure

Each challenge in the benchmark has:
```
{source}/{challenge_name}/
├── metadata/
│   └── metadata.json       # Contains: subtasks, difficulty, categories, prompts, flags
├── challenge/
│   └── (challenge files)   # Copied to workspace/challenge/ on setup
└── ...
```

The flag is extracted from the **last subtask's answer** in `metadata.json`.

## Tips

- **Flag format varies**: Could be `flag{...}`, `HTB{...}`, or other formats depending on the source CTF
- **Security tools**: The `cybench/cybench:latest` image includes common CTF tools
- **Write the exact flag**: No extra whitespace, no explanation — just the flag string
- **Some challenges may need network access**: Check if the container has internet connectivity
- **Challenge files on host**: `post_setup()` copies `challenge/` directory into the workspace — access them there or transfer into the container
