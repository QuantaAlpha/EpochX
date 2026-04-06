# EpochX Bench — Agent Execution Skill

> **给 AI Agent 的完整指南**: 如何用 `epochx bench` CLI 发现、执行、提交和验证 benchmark 任务。
> 每个 benchmark 有独立指南：[`benchmarks/`](benchmarks/)

---

## 0. Quick Start — 单任务端到端

> 按下面 6 步机械执行即可完成一个任务。

### Step 1: 确认 CLI 可用

```bash
epochx bench list >/dev/null 2>&1 && echo "CLI ready" || echo "Need install"
```

如果 `Need install`，在项目根目录（含 `pyproject.toml`）：
```bash
uv pip install -e .                # 基础安装（必须）
uv pip install -e ".[dabstep]"     # 跑 dabstep 时加装
uv pip install -e ".[swebench]"    # 跑 swebench-pro 时加装
```
> 只装要跑的 benchmark 依赖。没有 `uv` 时用 `pip` 代替。

### Step 2: 启动任务

```bash
epochx bench run {benchmark} --index {N} --json
# 或: epochx bench run {benchmark} --task {external_id} --json
```

从返回的 JSON 中提取两个关键变量：
```python
import json
result = json.loads(stdout)
task_id   = result["task_id"]    # e.g. "dabstep/5"
workspace = result["workspace"]  # e.g. "~/.epochx/arena/dabstep/5"
```

### Step 3: 读 prompt.md — 唯一信息源

```bash
cat {workspace}/.epochx/prompt.md
```

prompt.md 包含 **一切需要的信息**：任务描述、环境（Host 路径 / Docker SSH host + workdir）、输出要求、collect 命令。**不要猜测路径或 SSH host，全部从 prompt.md 读取。**

### Step 4: 解题

**Host 模式**（dabstep, tau-bench）：
```bash
cd {workspace}        # ⚠️ 必须先 cd 到 workspace
# 读数据、分析、写答案
echo "your_answer" > .epochx/answer.txt
```

**Docker 模式**（swebench-pro, cybench, da-code, core-bench）：
```bash
ssh {ssh_host}                   # prompt.md 里有
cd {container_workdir}           # prompt.md 里有
# 阅读代码、修复 bug、运行测试...
```

### Step 5: 收集 + 停止 + 评测

```bash
epochx bench collect {task_id}
epochx bench stop {task_id}
epochx bench grade {task_id}
```

### Step 6: 查看结果

```bash
cat {workspace}/.epochx/result.json
# {"passed": true, "score": 1.0, "details": {...}}
```

---

## 1. Core Concepts

### 1.1 Task ID

Full ID = `{benchmark}/{external_id}`（如 `dabstep/5`, `swebench-pro/django__django-16379`）。

- `--task` flag 接受 `external_id`
- `collect` / `grade` / `stop` 接受 **full ID**

### 1.2 Runtime Modes

| Mode | How to Execute |
|------|----------------|
| **Host** | `cd {workspace} && {command}` |
| **Docker** | `ssh {ssh_host} 'cd {container_workdir} && {command}'` |

> Docker 镜像的工作目录不同（`/app`, `/testbed`, `/workspace` 等），系统自动检测并写入 prompt.md。**始终从 prompt.md 读取，不要硬编码。**

### 1.3 Workspace Layout

每个任务独立在 `~/.epochx/arena/{benchmark}/{task_id}/`：

```
.epochx/
├── prompt.md       # 任务说明（唯一信息源）
├── meta.json       # 元数据
├── answer.txt      # ANSWER_STRING 输出
├── output.txt      # collect 写入的输出
└── result.json     # grade 写入的评测结果
```

> 每个任务完全隔离，可安全并行。

### 1.4 Output Types

| Type | What to Produce | Where to Write |
|------|----------------|----------------|
| `ANSWER_STRING` | 文本答案 | `.epochx/answer.txt` |
| `GIT_DIFF` | 代码修改 | 直接改代码（`collect` 自动 diff base commit） |
| `FILE_CONTENT` | 输出文件 | 见 prompt 指定路径 |
| `TRAJECTORY` | JSON 对话日志 | `.epochx/trajectory.json` |

---

## 2. CLI Reference

```bash
# 发现
epochx bench list [--json]                     # 所有 benchmark
epochx bench info {benchmark}                  # benchmark 详情
epochx bench tasks {benchmark} --limit 10      # 列出任务
epochx bench next {benchmark} [--json]         # 下一个未完成任务

# 生命周期: run → (解题) → collect → stop → grade
epochx bench run {benchmark} [--task {id}] [--index N] [--json]
epochx bench collect {full_task_id} [--json]
epochx bench stop {full_task_id} [--json]
epochx bench grade {full_task_id} [--json]

# 状态
epochx bench status [--json]
```

所有命令支持 `--json`，返回的 `status` 字段含义：

| Status | Meaning |
|--------|---------|
| `started` | 环境已创建 |
| `already_running` | 环境已存在，继续工作 |
| `collected` / `graded` / `stopped` | 对应操作完成 |
| `found` / `all_done` | next 命令：有/无下一个任务 |
| `error` | 出错，查看 `message` |

### Lifecycle 顺序说明

**collect → stop → grade**（不是 collect → grade → stop）：
- `collect`: 从 agent 容器中提取输出（SSH 取 git diff / 读 answer.txt）
- `stop`: 关闭 agent 容器，释放资源
- `grade`: Docker 模式下启动**全新评测容器**（还原基准 → 应用 patch → 跑测试），Host 模式下在本地评测

> 必须先 `collect` 再 `stop`，否则容器关了就无法提取输出。`grade` 不依赖 agent 容器。

---

## 3. Output Submission — 各类型写法

### ANSWER_STRING (dabstep, cybench)

```bash
# Host 模式
echo "42" > {workspace}/.epochx/answer.txt

# Docker 模式 — 通过 /.epochx 挂载
ssh {ssh_host} 'echo "flag{secret}" > /.epochx/answer.txt'
# 或直接在宿主机写
echo "flag{secret}" > {workspace}/.epochx/answer.txt
```

### GIT_DIFF (swebench-pro, swebench-verified)

```bash
ssh {ssh_host} 'bash -s' <<'SCRIPT'
cd {container_workdir}
# ... 修改源代码 ...
git add -A && git commit -m "fix: description"
SCRIPT
# collect 会自动 diff base_commit，不 commit 也能正确提取
```

### SNAPSHOT_DIFF (terminal-bench)

```bash
# Terminal-Bench 不需要写特定输出文件
# 直接在容器内完成任务，collect 时自动运行验证脚本
ssh {ssh_host} 'cd /app && ... (完成 instruction.md 中的任务)'
# collect 会通过 SSH 运行 test.sh，检查容器最终状态
```

### FILE_CONTENT (da-code, core-bench)

```bash
# 看 prompt 指定的输出路径
ssh {ssh_host} 'python3 solve.py > /.epochx/output.txt'
# CORE-Bench: 写到 results/ 目录
mkdir -p {workspace}/results && echo "data" > {workspace}/results/output.txt
```

### TRAJECTORY (tau-bench)

```bash
cat > {workspace}/.epochx/trajectory.json <<'EOF'
[
  {"role": "user", "content": "I need help with my booking"},
  {"role": "assistant", "content": "What's your booking reference?"}
]
EOF
```

---

## 4. Batch Workflow — 批量跑完一个 Benchmark

```bash
BENCHMARK="dabstep"

while true; do
  NEXT=$(epochx bench next "$BENCHMARK" --json)
  STATUS=$(echo "$NEXT" | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")
  [ "$STATUS" = "all_done" ] && break

  TASK_ID=$(echo "$NEXT" | python3 -c "import sys,json; print(json.load(sys.stdin)['task_id'])")
  CMD=$(echo "$NEXT" | python3 -c "import sys,json; print(json.load(sys.stdin)['start_command'])")

  eval "$CMD --json"
  # ... agent solves the task ...
  epochx bench collect "$TASK_ID"
  epochx bench stop "$TASK_ID"
  epochx bench grade "$TASK_ID"
done
```

### 汇总与导出

```bash
# 查看汇总报告（表格 + 逐任务详情）
epochx bench report
epochx bench report -b swebench-verified     # 只看某个 benchmark
epochx bench report --json                    # JSON 格式

# 导出到固定目录（用于提交 leaderboard）
epochx bench export --run-id my-run-v1
epochx bench export -b swebench-verified      # 只导出某个 benchmark
epochx bench export -o ./results              # 自定义输出目录
```

导出目录结构:
```
~/.epochx/exports/{run_id}/
├── summary.json              # 汇总统计（pass_rate, completed, pending...）
├── results.jsonl             # 所有任务结果（每行一个 JSON）
└── by_benchmark/
    ├── swebench-verified/
    │   ├── results.jsonl     # 该 benchmark 结果
    │   └── predictions.jsonl # SWE-bench 标准提交格式
    ├── terminal-bench/
    │   ├── results.jsonl
    │   └── predictions.jsonl
    └── ...
```

> `predictions.jsonl` 直接是各 leaderboard 要求的提交格式（如 SWE-bench 的 `instance_id` + `model_patch`）。

### 查看已有结果

```bash
# 所有运行中的环境
epochx bench status

# 单任务详情
cat ~/.epochx/arena/dabstep/5/.epochx/result.json
```

---

## 5. Docker Execution Guide

> 适用于: **swebench-pro**, **swebench-verified**, **terminal-bench**, **cybench**, **da-code**, **core-bench**

### SSH Access

prompt.md 里有完整的 SSH 信息。基本用法：

```bash
ssh {ssh_host}                                 # 交互
ssh {ssh_host} 'cd {container_workdir} && ls'  # 单命令
ssh {ssh_host} 'bash -s' <<'SCRIPT'            # 多行脚本
cd {container_workdir}
git status
SCRIPT
```

### File Transfer

`/.epochx` 是 bind mount（容器内 → 宿主机 `{workspace}/.epochx/`）：

```bash
# 宿主机写入 → 容器可读
cp myfile.txt {workspace}/.epochx/myfile.txt

# 容器写出 → 宿主机可读
ssh {ssh_host} 'cat /some/file > /.epochx/result.txt'
```

对于 `/.epochx` 之外的文件，用 `scp`：

```bash
scp {ssh_host}:{container_workdir}/output.py ./output.py
scp ./input.txt {ssh_host}:{container_workdir}/input.txt
```

### Container Details

- 命名: `epochx-{3char_prefix}-{8char_hash}` (如 `epochx-swe-a3f1c2d0`)
- SSH Key: `~/.ssh/epochx_key` (自动生成)
- Port: 22000-22999 (自动分配)
- User: `root`

### Troubleshooting

```bash
docker ps | grep epochx                    # 容器是否运行
ssh -v {ssh_host}                          # SSH 调试
docker exec -it {container_name} bash      # 绕过 SSH 直接进入
docker exec {container_name} /usr/sbin/sshd  # 重启 sshd
```

---

## 6. Grading

`epochx bench grade` 调用 **各 benchmark 自己的评测工具链**，不重写评测逻辑。

- **Host 模式** (dabstep, tau-bench): 本地精确匹配/脚本评测
- **Docker 模式** (swebench-pro 等): 启动**全新容器**，还原基准 → 应用 patch → 跑测试 → 收集结果

| Benchmark | 评测方式 |
|-----------|---------|
| **dabstep** | 精确匹配 |
| **swebench-pro** | Docker 内跑测试 (`swe_bench_pro_eval.py --use_local_docker`) |
| **swebench-verified** | 标准 swebench harness (`python -m swebench.harness.run_evaluation`) |
| **terminal-bench** | 容器内运行 test.sh，检查 reward.txt (1=pass, 0=fail) |
| **cybench** | 精确匹配 flag |
| **da-code** | 自定义评估器 |
| **core-bench** | 结果比对 |
| **tau-bench** | JSON 合法性检查 |

---

## 7. Error Recovery

| Symptom | Solution |
|---------|----------|
| `"status": "already_running"` | `stop` then re-`run` |
| `Docker image not found` | `run` 会自动 pull；手动: `docker pull {image}` |
| `SSH connection refused` | `docker exec {name} /usr/sbin/sshd` |
| `No output collected` | 检查是否写了输出文件，重新 `collect` |
| Container exited | `stop` then re-`run` |
| Port conflict | `rm ~/.epochx/ports.json` then re-`run` |

---

## 8. State & Cleanup

```
~/.epochx/
├── arena/          # 任务 workspace（每个任务独立自包含）
├── cache/          # 数据集缓存（加速启动）
├── exports/        # 导出结果（export 命令生成）
│   ├── latest -> {最新 run_id}/
│   └── {run_id}/
├── state.json      # 环境运行状态
└── ports.json      # SSH 端口分配
```

### 清理 Docker 镜像

Docker 镜像下载后会保留在本地（加速下次启动），但跑完大量任务后会占用较多磁盘。

```bash
# 查看各 benchmark 镜像占用空间（不删除）
epochx bench clean --dry-run

# 删除全部 benchmark 镜像
epochx bench clean

# 只删某个 benchmark 的镜像
epochx bench clean -b swebench-verified
epochx bench clean -b terminal-bench
```

### 完全清理

```bash
# 停止所有容器
docker ps --filter "name=epochx-" -q | xargs -r docker stop

# 清理运行状态（保留 Docker 镜像缓存和导出结果）
rm -rf ~/.epochx/arena ~/.epochx/state.json ~/.epochx/ports.json

# 清理一切（包括镜像、缓存、导出）
epochx bench clean
rm -rf ~/.epochx/arena ~/.epochx/state.json ~/.epochx/ports.json ~/.epochx/cache ~/.epochx/exports
```

---

## 9. Available Benchmarks

| Benchmark | Runtime | Tasks | Output Type | Guide |
|-----------|---------|-------|-------------|-------|
| **dabstep** | Host | 450 | ANSWER_STRING | [`benchmarks/dabstep.md`](benchmarks/dabstep.md) |
| **swebench-pro** | Docker | 731 | GIT_DIFF | [`benchmarks/swebench-pro.md`](benchmarks/swebench-pro.md) |
| **swebench-verified** | Docker | 500 | GIT_DIFF | [`benchmarks/swebench-verified.md`](benchmarks/swebench-verified.md) |
| **terminal-bench** | Docker | 89 | SNAPSHOT_DIFF | [`benchmarks/terminal-bench.md`](benchmarks/terminal-bench.md) |
| **cybench** | Docker | 40 | ANSWER_STRING | [`benchmarks/cybench.md`](benchmarks/cybench.md) |
| **da-code** | Docker | varies | FILE_CONTENT | [`benchmarks/da-code.md`](benchmarks/da-code.md) |
| **core-bench** | Docker | 90 | FILE_CONTENT | [`benchmarks/core-bench.md`](benchmarks/core-bench.md) |
| **tau-bench** | Host | varies | TRAJECTORY | [`benchmarks/tau-bench.md`](benchmarks/tau-bench.md) |

Platform integration: [`references/claude-code-integration.md`](references/claude-code-integration.md)
