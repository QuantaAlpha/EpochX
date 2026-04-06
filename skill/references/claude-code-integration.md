# Claude Code Integration Reference

> How to run epochx benchmarks with `claude -p` (Claude Code prompt mode).

## Single Task Execution

```bash
# 1. Start the task environment
RESULT=$(epochx bench run swebench-pro --task django__django-16379 --json)
WORKSPACE=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['workspace'])")
TASK_ID=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['task_id'])")

# 2. Read the generated prompt
PROMPT=$(cat "$WORKSPACE/.epochx/prompt.md")

# 3. Dispatch agent to solve
claude -p "$PROMPT" --model sonnet --dangerously-skip-permissions

# 4. Collect + Stop + Grade
epochx bench collect "$TASK_ID"
epochx bench stop "$TASK_ID"
epochx bench grade "$TASK_ID"
```

## Orchestrator Pattern (Batch All Tasks)

```bash
claude -p "You are a benchmark orchestrator for {benchmark}.

For each task:
1. epochx bench next {benchmark} --json → if 'all_done', stop
2. Start via the start_command from the response
3. Read {workspace}/.epochx/prompt.md
4. Solve the task
5. epochx bench collect {task_id} && epochx bench stop {task_id} && epochx bench grade {task_id}
6. Repeat

Use --json for all epochx commands to parse output reliably.
" --model sonnet --dangerously-skip-permissions
```

## With Budget Control

```bash
claude -p "$PROMPT" \
  --model sonnet \
  --max-budget-usd 5.00 \
  --dangerously-skip-permissions
```

## With Skill Injection

```bash
SKILL=$(cat docs/epochx_bench_agent_skill.md)
BENCH_GUIDE=$(cat docs/benchmarks/swebench-pro.md)
PROMPT=$(cat "$WORKSPACE/.epochx/prompt.md")

claude -p "## Skill Guide
$SKILL

## Benchmark Guide
$BENCH_GUIDE

## Task
$PROMPT" --model sonnet --dangerously-skip-permissions
```
