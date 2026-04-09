# EpochX CLI 命令与 Benchmark 流程说明

> 面向开发者的内部文档，帮助理解 CLI 命令、整体架构和 benchmark 执行流程。

## 目录

- [一、项目架构概览](#一项目架构概览)
- [二、核心概念](#二核心概念)
- [三、CLI 命令详解](#三cli-命令详解)
- [四、Benchmark 执行全流程](#四benchmark-执行全流程)
- [五、Adapter 架构与开发规范](#五adapter-架构与开发规范)
- [六、核心模块说明](#六核心模块说明)
- [七、数据结构与状态存储](#七数据结构与状态存储)

---

## 一、项目架构概览

```
src/epochx/
├── cli.py                    # CLI 入口 (Typer)，16 个命令
├── runner.py                 # 任务编排器 (run→collect→grade→stop)
├── exporter.py               # 结果导出 & 报告
├── core/
│   ├── task.py               # 数据模型 (Task, EvalResult, WorkspaceInfo 等)
│   ├── state.py              # Run-based 状态持久化 (~/.epochx/runs/)
│   ├── runtime.py            # 执行环境 (HostRuntime / DockerRuntime)
│   ├── port_manager.py       # Docker SSH 端口分配
│   └── prompt_generator.py   # Agent 提示词生成
├── adapters/
│   ├── base.py               # Adapter 抽象基类 + 注册表
│   ├── swebench_pro.py       # SWE-bench Pro
│   ├── swebench_verified.py  # SWE-bench Verified
│   ├── dabstep.py            # DABstep
│   ├── terminal_bench.py     # Terminal-Bench
│   ├── core_bench.py         # CORE-Bench
│   ├── cybench.py            # CyberArk Bench
│   ├── da_code.py            # DACode
│   └── tau_bench.py          # TAU-Bench
└── agents/
    ├── __init__.py
    └── base.py               # Agent 抽象基类
```

入口点定义在 `pyproject.toml`:

```toml
[project.scripts]
epochx-bench = "epochx.cli:main"
```

---

## 二、核心概念

### Run = 一次实验

**Run 是 EpochX 的核心组织单元**，代表一次完整的实验。一个 run：

- 不绑定任何特定 benchmark，可以在同一个 run 中跑多个 benchmark 的任务
- 拥有独立的状态文件 (`run.json`) 和工作区目录 (`arena/`)
- 不同 run 之间的数据完全隔离

本地目录结构：

```
~/.epochx/runs/
├── current -> agent-v2          # 符号链接，指向当前活跃 run
├── agent-v2/
│   ├── run.json                 # 状态：environments + results
│   └── arena/                   # 工作区
│       ├── swebench-pro/
│       │   └── django__django-16379/
│       └── dabstep/
│           └── 5/
└── agent-v1/
    ├── run.json
    └── arena/
```

**切换 run 的本质**就是把 `current` 符号链接指向另一个目录。所有命令都作用于 `current` 指向的 run。

---

## 三、CLI 命令详解

所有命令格式: `epochx-bench <command> [options]`

所有命令都支持 `--json` 参数，以 JSON 格式输出结果，方便程序化调用。

### Run 管理

#### `run-create` — 创建新实验

```bash
epochx-bench run-create [name] [--json]
```

| 参数 | 说明 |
|------|------|
| `name` | 可选，实验名称，默认自动生成 `run-{YYYYMMDD-HHMMSS}` |

创建一个新的 run 目录并设置为当前活跃 run。

> 注：`run` 命令在没有活跃 run 时会自动创建，因此 `run-create` 不是必须的前置步骤，但推荐用它来给实验起一个有意义的名字。

#### `run-list` — 列出所有实验

```bash
epochx-bench run-list [--json]
```

显示所有本地 run，包括名称、涉及的 benchmarks（从数据中聚合）、任务通过数/完成数、是否为当前 run。

#### `run-switch` — 切换当前实验

```bash
epochx-bench run-switch <run_name> [--json]
```

切换当前活跃 run。后续所有命令都作用于新 run。

### Benchmark 查询

#### `list` — 列出所有可用 benchmark

```bash
epochx-bench list [--json]
```

显示所有已注册 benchmark 的名称、描述、运行时类型、资源需求等信息。

#### `info` — 查看 benchmark 详情

```bash
epochx-bench info <benchmark> [--json]
```

返回该 benchmark 的详细元数据。

#### `tasks` — 列出 benchmark 的任务列表

```bash
epochx-bench tasks <benchmark> [--limit 20] [--json]
```

显示每个任务的 ID、外部 ID、输出类型。

#### `next` — 获取下一个待执行任务

```bash
epochx-bench next <benchmark> [--json]
```

从当前 run 中排除已运行和已完成的任务，返回第一个待执行任务。

### 任务生命周期

#### `run` — 启动任务环境

```bash
epochx-bench run <benchmark> [--task <id>] [--index <n>] [--json]
```

| 参数 | 说明 |
|------|------|
| `benchmark` | benchmark 名称 |
| `--task` | 指定任务 ID |
| `--index` | 指定任务序号 |

**执行流程:**

1. 检查当前 run，没有则自动创建
2. 解析要运行的任务 (task_id > index > 第一个可用)
3. 检查是否已在运行
4. 拉取/构建 Docker 镜像 (如需要)
5. 创建运行时环境 (Host / Docker)
6. 初始化工作区 (克隆仓库 / 拷贝数据)
7. 写入 `.epochx/prompt.md` 和 `.epochx/meta.json`
8. 持久化环境状态到当前 run

**返回:** task_id、workspace 路径、prompt 文件位置、下一步命令。

#### `collect` — 收集 Agent 输出

```bash
epochx-bench collect <task_id> [--json]
```

从工作区提取 Agent 的解决方案 (Docker 通过 SSH，Host 直接读文件系统)。输出保存到 `.epochx/output.txt`。

#### `grade` — 评估输出结果

```bash
epochx-bench grade <task_id> [--json]
```

调用 adapter 的 `evaluate()` 进行评分。结果保存到 `.epochx/result.json`，状态更新为 `COMPLETED` 或 `FAILED`。

#### `stop` — 停止并清理任务

```bash
epochx-bench stop <task_id> [--json]
```

停止 Docker 容器、释放 SSH 端口、更新状态为 `STOPPED`。

#### `status` — 查看运行中的任务

```bash
epochx-bench status [--json]
```

显示当前 run 中所有任务环境的状态。

### 结果与提交

#### `report` — 查看结果报告

```bash
epochx-bench report [--benchmark <name>] [--all] [--json]
```

| 参数 | 说明 |
|------|------|
| `--benchmark, -b` | 按 benchmark 过滤 |
| `--all` | 显示所有 run 的结果 |

默认显示当前 run 的聚合结果 (按 benchmark 分组的通过率、进度条、任务明细)。`--all` 遍历所有 run 分别输出。

#### `export` — 导出结果

```bash
epochx-bench export [--benchmark <name>] [--run-id <id>] [--output-dir <path>] [--json]
```

生成结构化导出目录:

```
output_dir/
├── results.jsonl                 # 所有任务结果
├── summary.json                  # 聚合统计
└── by_benchmark/
    ├── swebench-pro/
    │   ├── results.jsonl
    │   └── predictions.jsonl     # 提交格式 (patch)
    └── dabstep/
        ├── results.jsonl
        └── predictions.jsonl     # 提交格式 (answer)
```

#### `submit-run` — 提交结果到 EpochX Arena

```bash
epochx-bench submit-run [--benchmark <name>] [--api-key <key>] [--model <name>] [--version <v>] [--run <run_name>] [--json]
```

| 参数 | 说明 |
|------|------|
| `--api-key` | EpochX API key，默认读取 `~/.epochx/config.json` |
| `--api-url` | API 地址，默认 `https://epochx.cc` |
| `--model` | Agent 模型名 |
| `--version, -v` | Agent 版本号 |
| `--run` | 指定提交的 run (默认: 当前 run) |

提交时 `run_name` 自动使用当前 run 的名字。将结果 POST 到 `/api/v1/arena/runs`，返回 run_id 和排行榜链接。

#### `clean` — 清理 Docker 镜像

```bash
epochx-bench clean [--benchmark <name>] [--dry-run] [--json]
```

删除 benchmark 相关的 Docker 镜像以释放磁盘空间。

---

## 四、Benchmark 执行全流程

### 4.1 流程图

```
                    ┌──────────────────┐
                    │  list / info     │   浏览可用 benchmark
                    └──────┬───────────┘
                           │
                    ┌──────▼───────────┐
                    │  run-create      │   创建实验 (可选)
                    └──────┬───────────┘
                           │
                    ┌──────▼───────────┐
                    │  next / tasks    │   选择任务
                    └──────┬───────────┘
                           │
                    ┌──────▼───────────┐
                    │     run          │   启动环境
                    └──────┬───────────┘
                           │
               ┌───────────▼───────────┐
               │  Agent 在环境中工作    │   读取 prompt，修改代码
               └───────────┬───────────┘
                           │
                    ┌──────▼───────────┐
                    │   collect        │   提取输出
                    └──────┬───────────┘
                           │
                    ┌──────▼───────────┐
                    │    grade         │   评分
                    └──────┬───────────┘
                           │
                    ┌──────▼───────────┐
                    │    stop          │   清理资源
                    └──────┬───────────┘
                           │
               ┌───────────▼───────────┐
               │  report / export /    │   查看 / 导出 / 提交
               │  submit-run           │
               └───────────────────────┘
```

### 4.2 典型交互会话

```bash
# 创建实验
epochx-bench run-create "agent-v2-experiment"

# 在同一实验中跑多个 benchmark
epochx-bench run swebench-pro --task django__django-16379
epochx-bench collect swebench-pro/django__django-16379
epochx-bench grade swebench-pro/django__django-16379
epochx-bench stop swebench-pro/django__django-16379

epochx-bench run dabstep --task 5
epochx-bench collect dabstep/5
epochx-bench grade dabstep/5

# 查看报告
epochx-bench report

# 提交到 Arena (run_name 自动为 "agent-v2-experiment")
epochx-bench submit-run --model claude-sonnet-4-20250514
```

### 4.3 多实验管理

```bash
# 列出所有实验
epochx-bench run-list

# 创建新实验
epochx-bench run-create "agent-v3"

# 切换回旧实验
epochx-bench run-switch agent-v2-experiment

# 查看所有实验结果
epochx-bench report --all

# 跨 run 提交 (不需要切换)
epochx-bench submit-run --run agent-v2-experiment
```

### 4.4 任务状态流转

```
PENDING → RUNNING → COLLECTING → GRADING → COMPLETED
                                         → FAILED
              ↓ (手动停止)
           STOPPED
```

---

## 五、Adapter 架构与开发规范

### 5.1 Adapter 接口

每个 benchmark 对应一个 Adapter，继承 `BenchmarkAdapter` 基类:

```python
@register_adapter
class MyBenchAdapter(BenchmarkAdapter):
    name = "my-bench"
    display_name = "My Benchmark"
    description = "..."
    agent_runtime = RuntimeType.DOCKER  # or HOST
    eval_runtime = RuntimeType.DOCKER
    resource_profile = "medium"  # light / medium / heavy

    def fetch_tasks(self, limit=None, task_ids=None) -> list[Task]:
        """加载任务定义"""

    def collect_output(self, workspace_path, task, env=None) -> str:
        """从工作区提取 Agent 输出"""

    def evaluate(self, task, output) -> EvalResult:
        """评估 Agent 输出"""

    # 可选
    def prepare_image(self, task) -> str | None:
        """拉取/构建 Docker 镜像"""

    def post_setup(self, workspace_path, task) -> None:
        """工作区创建后的 hook"""
```

### 5.2 开发规范

1. **`evaluate()` 必须复用官方评测工具** — 禁止重新实现评测逻辑
2. **Docker 任务的 `collect_output()` 必须通过 SSH** — 仅 HOST 运行时才直接读文件系统
3. **Task ID 格式**: `{benchmark}/{external_id}`，如 `swebench-pro/django__django-16379`

### 5.3 现有 Adapter 一览

| Adapter | 运行时 | 评估方式 | 任务数 | 数据来源 |
|---------|--------|---------|--------|---------|
| swebench-pro | DOCKER | subprocess → swe_bench_pro_eval.py | 731 | DockerHub 预构建镜像 |
| swebench-verified | DOCKER | swebench 官方 harness | 500 | DockerHub 标准镜像 |
| dabstep | HOST | exact-match (进程内) | 450 | 本地 JSON |
| terminal-bench | DOCKER | Docker test 验证 | 89+ | TOML 配置 |
| core-bench | DOCKER | Vision+Text 评分 (DinD) | 90 | JSON + Docker |
| cybench | DOCKER | 自定义评分脚本 | - | JSON 配置 |
| da_code | DOCKER | subprocess 评估 | - | HuggingFace Dataset |
| tau-bench | HOST | 自动化结果评分 | - | JSON |

---

## 六、核心模块说明

### 6.1 `core/task.py` — 数据模型

关键枚举:
- **WorkspaceType**: `GIT_REPO` / `DATA_DIR` / `MCP_ENV` / `API_ONLY`
- **OutputType**: `GIT_DIFF` / `FILE_CONTENT` / `ANSWER_STRING` / `TRAJECTORY` / `SNAPSHOT_DIFF`
- **EvalType**: `DOCKER_TEST` / `EXACT_MATCH` / `LLM_JUDGE` / `REWARD_FUNCTION` / `CUSTOM_SCRIPT`
- **RuntimeType**: `HOST` / `UV` / `DOCKER`
- **TaskStatus**: `PENDING` / `RUNNING` / `COLLECTING` / `GRADING` / `COMPLETED` / `FAILED` / `STOPPED`

关键数据类:
- **Task**: 完整任务定义 (WorkspaceSpec + OutputSpec + EvalSpec)
- **EvalResult**: 评分结果 (passed, score, details, error)
- **WorkspaceInfo**: 运行时工作区信息 (path, ssh_host, ssh_port, container_id)

### 6.2 `core/state.py` — Run-based 状态管理

`StateManager` 通过 `~/.epochx/runs/` 下的目录 + `current` 符号链接管理状态：

- `create_run(name)` — 创建目录，写空 `run.json`，`current` 指过去
- `switch_run(name)` — 把 `current` 符号链接指向目标 run 目录
- `current_run_name()` — 读 `current` 链接的目标目录名
- `list_runs()` — 遍历目录，从 environments/results 中聚合 benchmarks
- `save_environment()` / `get_environment()` — 读写当前 run 的环境状态
- `save_result()` / `get_results()` — 读写当前 run 的评测结果

**自动迁移:** 检测到旧版 `~/.epochx/state.json` 时，自动迁移到 `runs/default/run.json`。

### 6.3 `core/runtime.py` — 执行环境

- **HostRuntime**: 宿主机上创建工作区和执行命令
- **DockerRuntime**: 启动容器 + SSH 通道
- **RuntimeFactory**: 根据 RuntimeType 实例化

### 6.4 `core/port_manager.py` — 端口管理

Docker 容器 SSH 端口分配 (22000-22999)，持久化在 `~/.epochx/ports.json`。

### 6.5 `runner.py` — 任务编排器

`BenchRunner` 串联生命周期:
- `run_task()` — 没有活跃 run 时自动创建，然后启动任务环境
- `collect_task()` → `grade_task()` → `stop_task()`
- `get_next_task()` — 基于当前 run 的状态跳过已完成的任务

工作区路径通过 `state.get_arena_dir()` 获取，不同 run 之间工作区隔离。

### 6.6 `exporter.py` — 导出与报告

- **Reporter**: 聚合统计 (通过率、完成数等)
- **Exporter**: 生成结构化导出目录，支持各 benchmark 官方提交格式

---

## 七、数据结构与状态存储

### 7.1 `run.json`

```json
{
  "run_name": "agent-v2",
  "created_at": "2026-04-08T10:30:00+00:00",
  "environments": {
    "swebench-pro/django__django-16379": {
      "task_id": "swebench-pro/django__django-16379",
      "benchmark": "swebench-pro",
      "workspace": "~/.epochx/runs/agent-v2/arena/swebench-pro/django__django-16379",
      "status": "completed",
      "container_id": "abc123...",
      "ssh_port": 22045,
      "ssh_host": "epochx-swe-a1b2c3d4",
      "container_workdir": "/testbed",
      "runtime": "docker",
      "started_at": "2026-04-08T10:30:00+00:00",
      "metadata": {}
    }
  },
  "results": {
    "swebench-pro/django__django-16379": {
      "task_id": "swebench-pro/django__django-16379",
      "passed": true,
      "score": 1.0,
      "benchmark": "swebench-pro",
      "details": { "tests_passed": 15, "tests_failed": 0 }
    }
  }
}
```

`run.json` 不存储 benchmark 字段，涉及哪些 benchmark 由 environments 和 results 决定。

### 7.2 工作区 `.epochx/` 目录

每个任务工作区下：

```
.epochx/
├── meta.json       # 任务元数据
├── prompt.md       # Agent 指令
├── output.txt      # 收集到的 Agent 输出
└── result.json     # 评估结果
```

### 7.3 全局配置文件

**`~/.epochx/config.json`** — 用户配置:

```json
{
  "api_key": "ah_xxxx",
  "api_url": "https://epochx.cc"
}
```

**`~/.epochx/ports.json`** — SSH 端口分配:

```json
{
  "swebench-pro/django__django-16379": 22045
}
```

### 7.4 旧版迁移

首次运行时检测到 `~/.epochx/state.json`，自动：

1. 创建 `runs/default/run.json`，写入旧数据
2. 移动 `~/.epochx/arena/` 到 `runs/default/arena/`
3. `current` 指向 `default`
4. 删除旧 `state.json`
