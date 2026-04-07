# DABstep — Benchmark Guide

> Financial data analysis benchmark — 450 tasks (easy + hard), exact-match scoring.

## Overview

| Item | Value |
|------|-------|
| **Name** | `dabstep` |
| **Runtime** | Host (no Docker) |
| **Tasks** | 450 (from `dev.jsonl`) |
| **Output Type** | `ANSWER_STRING` |
| **Answer File** | `.epochx/answer.txt` |
| **Evaluation** | Exact string match (case-sensitive, whitespace-trimmed) |
| **Resource Profile** | `light` |

## Data Source

Tasks are loaded from:
```
benchmarks/dabstep/repo/data/tasks/dev.jsonl    # Primary (has answers)
benchmarks/dabstep/repo/data/tasks/all.jsonl    # Fallback
```

Context data files (CSVs, etc.) are in:
```
benchmarks/dabstep/repo/data/context/
```

## Quick Start

```bash
# Start a task
epochx-bench run dabstep --task 5 --json

# Or start first available
epochx-bench run dabstep --json
```

## Workspace After Setup

```
{workspace}/
├── .epochx/
│   ├── meta.json
│   ├── prompt.md      # Contains: question, guidelines, available file list
│   └── answer.txt     # ← WRITE YOUR ANSWER HERE
└── data/
    ├── file1.csv      # Context data files (copied from benchmarks/dabstep/repo/data/context/)
    ├── file2.csv
    └── ...
```

## How to Solve

1. **Read the prompt**: `cat {workspace}/.epochx/prompt.md`
   - Contains a financial data analysis question
   - Includes guidelines on how to approach it
   - Lists available data files

2. **Analyze the data**: Files are in `{workspace}/data/`
   ```bash
   cd {workspace}
   ls data/                           # See available files
   head -5 data/some_file.csv         # Preview data
   python3 -c "import pandas as pd; print(pd.read_csv('data/some_file.csv').describe())"
   ```

3. **Write your answer**: A single string, nothing else
   ```bash
   echo "Yes" > {workspace}/.epochx/answer.txt
   ```

## Answer Format

- The answer must be an **exact string** (case-sensitive)
- Common answer types: numbers (`42`), text (`Yes`, `No`), percentages (`12.5%`)
- **Strip** any extra whitespace — only the answer, no explanation
- Do NOT include units unless the prompt says to

## Collect + Grade + Stop

```bash
epochx-bench collect dabstep/5
epochx-bench grade dabstep/5       # → {"passed": true/false, "score": 1.0/0.0}
epochx-bench stop dabstep/5
```

## Task Metadata

Each task has:
- `level`: "easy" or "hard"
- `guidelines`: Detailed instructions on how to approach the question
- `answer`: Expected answer (used for grading)

## Example

```
Question: "What is the average transaction amount in Q3 2023?"
Guidelines: "Use the transactions.csv file. Filter by date between 2023-07-01 and 2023-09-30. Round to 2 decimal places."
Answer: "1234.56"
```

## Tips

- Read the guidelines carefully — they specify rounding, format, filters
- Most answers are short strings (a word, number, or short phrase)
- Check all available CSV files before answering — some questions require joining data
- The `pandas` library is useful for data analysis (install if not available: `pip install pandas`)
