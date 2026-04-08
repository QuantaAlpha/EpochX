# 文明进化实验 Benchmark 全景调研报告

> 调研时间：2026-04-05 | 覆盖 2024-2026 年所有主要 Agent Benchmark
> 按 require.md 八大赛道分类，含链接、Docker 需求、SOTA、使用方式

---

## 零、影响力排行榜（按综合影响力排序）

> 综合影响力 = GitHub Stars + HuggingFace 下载量 + 学术引用数 + 行业采纳度 + 媒体曝光度

| 排名 | Benchmark | GitHub Stars | HF 下载量 | 学术引用 | 行业采纳 | 综合影响力 | 赛道 |
|:---:|-----------|:-----------:|:---------:|:-------:|:--------:|:---------:|------|
| 1 | **SWE-bench** (含Verified/Live/Pro全系) | 4,612 | 140,498 | 1,794 | ⭐⭐⭐⭐⭐ 所有头部公司必报 | ★★★★★ | 代码 |
| 2 | **Aider Polyglot** (aider工具本身) | 42,822 | — | — | ⭐⭐⭐⭐ 开发者社区标杆 | ★★★★★ | 代码 |
| 3 | **Gorilla / BFCL** | 12,797 | 71,392 | — | ⭐⭐⭐⭐ 函数调用事实标准 | ★★★★☆ | 工具调用 |
| 4 | **HumanEval** (参考/已饱和) | — | — | 8,889 | ⭐⭐⭐ 历史标杆但已饱和 | ★★★★☆ | 代码(旧) |
| 5 | **ToolBench / ToolLLM** | 5,588 | — | 1,334 | ⭐⭐⭐ 学术引用极高 | ★★★★☆ | 工具调用 |
| 6 | **WebArena** | 1,418 | — | 1,062 | ⭐⭐⭐⭐ Computer Use核心基准 | ★★★★☆ | Web |
| 7 | **AgentBench** | 3,299 | — | 659 | ⭐⭐⭐ 首批系统Agent评测 | ★★★☆☆ | 综合 |
| 8 | **OSWorld** | 2,736 | — | 530 | ⭐⭐⭐ Computer Use双支柱 | ★★★☆☆ | 桌面OS |
| 9 | **Terminal-Bench** | 1,877 | — | 36 | ⭐⭐⭐ Artificial Analysis采纳 | ★★★☆☆ | 终端 |
| 10 | **GAIA** | — | 33,822 | 634 | ⭐⭐⭐⭐ Meta/HF背书 | ★★★☆☆ | 通用助理 |
| 11 | **MLE-bench** | 1,440 | — | 181 | ⭐⭐⭐ OpenAI出品 | ★★★☆☆ | ML工程 |
| 12 | **DAMO-ConvAI / API-Bank** | 1,539 | — | — | ⭐⭐ 工具调用早期工作 | ★★☆☆☆ | 工具调用 |
| 13 | **tau-bench** | 1,160 | — | — | ⭐⭐ Sierra Research | ★★☆☆☆ | 客服对话 |
| 14 | **BrowserGym** | 1,186 | — | — | ⭐⭐⭐ Web Agent统一框架 | ★★☆☆☆ | Web框架 |
| 15 | **PaperBench** | 1,151 | — | ~100 | ⭐⭐⭐ OpenAI出品+ICML 2025 | ★★☆☆☆ | 科研复现 |
| 16 | **Mind2Web** | 970 | — | — | ⭐⭐ NeurIPS 2023 Spotlight | ★★☆☆☆ | Web |
| 17 | **SkillsBench** | 909 | — | 15 | ⭐⭐ 文明层核心+2026新 | ★★☆☆☆ | Skill增益 |
| 18 | **WindowsAgentArena** | 849 | — | — | ⭐⭐ Microsoft出品 | ★★☆☆☆ | 桌面OS |
| 19 | **LiveCodeBench** | 834 | — | — | ⭐⭐ 滚动更新 | ★★☆☆☆ | 代码 |
| 20 | **TheAgentCompany** | 671 | — | 131 | ⭐⭐ 企业SaaS场景 | ★★☆☆☆ | Web/企业 |
| 21 | **BigCodeBench** | 487 | — | 452 | ⭐⭐⭐ HumanEval替代 | ★★☆☆☆ | 代码 |
| 22 | **VisualWebArena** | 454 | — | — | ⭐⭐ 多模态Web | ★★☆☆☆ | Web(视觉) |
| 23 | **MLAgentBench** | 337 | — | — | ⭐⭐ Stanford SNAP | ★☆☆☆☆ | ML工程 |
| 24 | **SWE-bench Pro** | 334 | — | — | ⭐⭐⭐ OpenAI推荐替代 | ★☆☆☆☆ | 代码 |
| 25 | **ML-Bench** | 316 | — | — | ⭐ Yale Gerstein Lab | ★☆☆☆☆ | ML代码 |
| 26 | **ITBench** | 316 | — | 24 | ⭐⭐ IBM+ICML 2025 Oral | ★☆☆☆☆ | 终端/IT |
| 27 | **InterCode** | 245 | — | — | ⭐ NeurIPS 2023 | ★☆☆☆☆ | 交互编码 |
| 28 | **WorkArena** | 242 | — | — | ⭐⭐ ServiceNow | ★☆☆☆☆ | 企业SaaS |
| 29 | **Cybench** | 217 | — | — | ⭐ ICLR 2025 | ★☆☆☆☆ | 安全 |
| 30 | **SWE-bench Live** | 174 | — | — | ⭐⭐⭐ 微软+滚动更新 | ★☆☆☆☆ | 代码 |
| 31 | **CRUXEval** | 169 | 5,959 | — | ⭐ Meta/ICML 2024 | ★☆☆☆☆ | 代码推理 |
| 32 | **SheetCopilot** | 163 | — | — | ⭐ NeurIPS 2023 | ★☆☆☆☆ | 表格 |
| 33 | **SpreadsheetBench** | 144 | 2,230 | 32 | ⭐ NeurIPS 2024 Spotlight | ★☆☆☆☆ | 表格/BI |
| 34 | **RE-Bench** | 134 | — | — | ⭐⭐ METR | ★☆☆☆☆ | AI R&D |
| 35 | **ScienceAgentBench** | 133 | 1,181 | — | ⭐ ICLR 2025 | ★☆☆☆☆ | 科研 |
| 36 | **DSBench** | 111 | — | — | ⭐ ICLR 2025 | ★☆☆☆☆ | 数据科学 |
| 37 | **DataSciBench** | 55 | — | — | ⭐ 清华THUDM | ★☆☆☆☆ | 数据科学 |
| 38 | **OpsEval** | 51 | — | — | ⭐ 清华NetMan | ★☆☆☆☆ | IT运维知识 |
| 39 | **OfficeBench** | 34 | — | — | ⭐ | ★☆☆☆☆ | 办公 |
| 40 | **LMR-Bench** | 10 | — | — | ⭐ EMNLP 2025 | ★☆☆☆☆ | 论文复现 |

> 注：
> - SWE-bench HF下载量 = princeton-nlp/SWE-bench(20,322) + SWE-bench_Verified(120,176) = 140,498
> - Aider 的 42,822 stars 是整个 aider 工具（含benchmark），不只是benchmark本身
> - 部分新 benchmark（2025-2026发布）引用数和stars自然较低，但增速快

### 影响力 vs 实验价值矩阵

```
影响力高 + 实验价值高（首选）          影响力高 + 实验价值低（参考）
┌─────────────────────────────┐    ┌──────────────────────────┐
│ SWE-bench Live/Pro          │    │ HumanEval (已饱和)       │
│ WebArena                    │    │ Aider Polyglot (非Agent) │
│ Terminal-Bench              │    │ AgentBench (被分流)      │
│ MLE-bench                   │    │                          │
│ GAIA                        │    │                          │
│ OSWorld                     │    │                          │
└─────────────────────────────┘    └──────────────────────────┘

影响力低 + 实验价值高（潜力股）        影响力低 + 实验价值低（可跳过）
┌─────────────────────────────┐    ┌──────────────────────────┐
│ SkillsBench (文明层核心!)   │    │ CRUXEval                 │
│ PaperBench                  │    │ SheetCopilot             │
│ TheAgentCompany             │    │ OpsEval                  │
│ SpreadsheetBench            │    │ API-Bank                 │
│ ITBench                     │    │ InterCode (质量差)       │
│ RE-Bench                    │    │ DataSciBench             │
│ LMR-Bench                   │    │                          │
│ DSBench                     │    │                          │
└─────────────────────────────┘    └──────────────────────────┘
```

### 关键洞察

1. **SWE-bench 生态是绝对霸主**：Stars 4,612 + HF下载 14万 + 引用 1,794 + 所有头部公司必报，无可争议的 #1
2. **影响力和实验价值不完全正相关**：HumanEval 引用最高(8,889)但已饱和；SkillsBench stars 909但对文明实验价值最高
3. **"潜力股"象限是 EpochX 的机会**：SkillsBench、PaperBench、TheAgentCompany、SpreadsheetBench 都是影响力正在快速增长的新 benchmark
4. **SWE-bench Live(174 stars) vs SWE-bench Original(4,612 stars)**：Live 虽然 stars 低，但技术上更先进（滚动更新+抗污染），stars 低是因为发布较新
5. **Gorilla/BFCL(12,797 stars)** 被低估：它是函数调用领域的事实标准，对 Skill 调用评估非常重要

---

## 一、总览：所有 Benchmark 一览表

| # | Benchmark | 赛道 | 任务数 | Docker | 隐藏测试 | 抗污染 | SOTA | GitHub / 官网 |
|---|-----------|------|--------|--------|----------|--------|------|--------------|
| 1 | SWE-bench Live | 代码 | ~1,890（月增50） | ✅ | ✅ | ✅ 强 | ~50% | [GitHub](https://github.com/microsoft/SWE-bench-Live) |
| 2 | SWE-bench Pro | 代码 | 1,865 | ✅ | ✅ | ✅ 强 | ~23% | [GitHub](https://github.com/scaleapi/SWE-bench_Pro-os) |
| 3 | SWE-bench Original | 代码 | 2,294 | ✅ | ✅ | ❌ | ~55% | [GitHub](https://github.com/SWE-bench/SWE-bench) |
| 4 | SWE-bench Multimodal | 代码(视觉) | 617 | ✅ | ✅ | 中 | <20% | [官网](https://www.swebench.com/multimodal.html) |
| 5 | SWE-rebench | 代码 | 21,000+ | ✅ | ✅ | ✅ | — | [HuggingFace](https://huggingface.co/datasets/nebius/SWE-rebench) |
| 6 | SWE-bench Verified | 代码 | 500 | ✅ | ✅ | ❌ 已弃用 | ~72% | [HuggingFace](https://huggingface.co/datasets/SWE-bench/SWE-bench_Verified) |
| 7 | SWE-Bench++ | 代码 | 11,133 | ✅ | ✅ | 中 | — | [arXiv](https://arxiv.org/abs/2512.17419) |
| 8 | Terminal-Bench 2.0 | 终端 | 89 | ✅ | ✅ | ✅ | 63% (Codex CLI+GPT-5.2) | [GitHub](https://github.com/laude-institute/terminal-bench) |
| 9 | ITBench | 终端/IT运维 | 102 | ✅ K8s | ✅ | ✅ | 11-26% | [GitHub](https://github.com/itbench-hub/ITBench) |
| 10 | DevOps-Gym | 终端/DevOps | 700+ | ✅ | ✅ | ✅ | — | [arXiv](https://arxiv.org/abs/2601.20882) |
| 11 | TB-Science | 终端/科学 | 100+（目标） | ✅ | ✅ | ✅ | 未发布 | [官网](https://www.tbench.ai/news/tb-science-announcement) |
| 12 | Cybench | 终端/安全 | 40 | ✅ | ✅ | ✅ | — | [GitHub](https://github.com/andyzorigin/cybench) |
| 13 | MLE-bench | ML工程 | 75 竞赛 | ✅ | ✅ | 中 | 34.1% pass@8 (o1+AIDE) | [GitHub](https://github.com/openai/mle-bench) |
| 14 | DSBench | ML/数据科学 | 540 | ❌ | 部分 | 中 | 34.12% | [GitHub](https://github.com/LiqiangJing/DSBench) |
| 15 | MLAgentBench | ML工程 | 13 | 推荐 | ✅ | 中 | 37.5% (Claude 3 Opus) | [GitHub](https://github.com/snap-stanford/MLAgentBench) |
| 16 | ML-Bench | ML代码 | 9,641 | 沙箱 | ❌ | 中 | 76.47% (GPT-4o) | [GitHub](https://github.com/gersteinlab/ML-Bench) |
| 17 | DataSciBench | 数据科学 | 222/519 | ❌ | 验证式 | 中 | — | [GitHub](https://github.com/THUDM/DataSciBench) |
| 18 | ScienceAgentBench | 科研 | 102 | ✅ | ✅ | ✅ | 42.2% (o1+self-debug) | [GitHub](https://github.com/OSU-NLP-Group/ScienceAgentBench) |
| 19 | SpreadsheetBench | 表格/BI | 912/2,729 | ✅ | ✅ | 中 | — | [GitHub](https://github.com/RUCKBReasoning/SpreadsheetBench) |
| 20 | OfficeBench | 办公 | 300 | ✅ | ❌ | 中 | 47% (GPT-4o) | [GitHub](https://github.com/zlwang-cs/OfficeBench) |
| 21 | OdysseyBench | 办公 | 602 | 未确认 | 未确认 | — | — | [arXiv](https://arxiv.org/abs/2508.09124) |
| 22 | SheetCopilot | 表格 | 221 | ❌ | ❌ | — | — | [GitHub](https://github.com/BraveGroup/SheetCopilot) |
| 23 | WebArena | Web | 812 | ✅ 6容器 | Verified版 | 中 | ~35% | [GitHub](https://github.com/web-arena-x/webarena) |
| 24 | VisualWebArena | Web(视觉) | 910 | ✅ | ❌ | 中 | ~20% | [GitHub](https://github.com/web-arena-x/visualwebarena) |
| 25 | TheAgentCompany | Web/企业 | 175 | ✅ 多服务 | ✅ 加密 | ✅ | 30.3% (Gemini 2.5 Pro) | [GitHub](https://github.com/TheAgentCompany/TheAgentCompany) |
| 26 | OSWorld | 桌面OS | 369 | VM | ✅ | ✅ | 12.24% | [GitHub](https://github.com/xlang-ai/OSWorld) |
| 27 | WorkArena | 企业SaaS | 33模板/19,912 | ❌ 需SN | ❌ | 中 | — | [GitHub](https://github.com/ServiceNow/WorkArena) |
| 28 | Mind2Web | Web浏览 | 2,350+ | ❌ | ✅ | 中 | — | [GitHub](https://github.com/OSU-NLP-Group/Mind2Web) |
| 29 | GAIA | 通用助理 | 466 | ❌ | ✅ ~300题 | ❌ 验证集已污染 | ~75% L1 | [HuggingFace](https://huggingface.co/datasets/gaia-benchmark/GAIA) |
| 30 | AgentBench | 综合8环境 | 数百 | ✅ | 部分 | 中 | — | [GitHub](https://github.com/THUDM/AgentBench) |
| 31 | tau-bench | 客服对话 | 164+ | ❌ | ✅ POMDP | ✅ | — | [GitHub](https://github.com/sierra-research/tau-bench) |
| 32 | PaperBench | 科研复现 | 20论文/8,316子任务 | ✅ 三容器 | ✅ | ✅ | 21-27% (Claude 3.5) | [GitHub](https://github.com/openai/preparedness/tree/main/project/paperbench) |
| 33 | SkillsBench | Skill增益 | 84任务/47,150 Skills | ❌ | ❌ | ✅ | +12.66pp 平均增益 | [GitHub](https://github.com/benchflow-ai/skillsbench) |
| 34 | RE-Bench | AI R&D | 7 | ✅ | ✅ | ✅ | Agent 2h = 4x 人类 | [GitHub](https://github.com/METR/RE-Bench) |
| 35 | LMR-Bench | 论文复现 | 28 | ✅ | ✅ | ✅ | — | [GitHub](https://github.com/du-nlp-lab/LMR-Bench) |
| 36 | BigCodeBench | 代码生成 | 1,140 | ✅ | ✅ | 中 | ~60% | [GitHub](https://github.com/bigcode-project/bigcodebench) |
| 37 | LiveCodeBench | 代码(滚动) | 1,055+（持续增长） | ✅ | ✅ | ✅ 滚动 | — | [GitHub](https://github.com/LiveCodeBench/LiveCodeBench) |
| 38 | Aider Polyglot | 代码(多语言) | 225 | ❌ | ✅ | 中 | ~88% (Claude Opus 4.6) | [官网](https://aider.chat/docs/leaderboards/) |
| 39 | CRUXEval | 代码推理 | 800 | ❌ | ❌ | — | 81.9% (GPT-4 CoT) | [GitHub](https://github.com/facebookresearch/cruxeval) |
| 40 | ToolBench | 工具调用 | 16,464 API | ❌ | ❌ | 中 | — | [GitHub](https://github.com/OpenBMB/ToolBench) |
| 41 | BFCL v4 | 函数调用 | 2,000+ | ❌ | ❌ | ✅ | — | [排行榜](https://gorilla.cs.berkeley.edu/leaderboard.html) |
| 42 | API-Bank | API调用 | 73 API/314对话 | ❌ | ❌ | — | — | [GitHub](https://github.com/AlibabaResearch/DAMO-ConvAI/tree/main/api-bank) |
| 43 | InterCode | 交互编码 | 5环境 | ✅ | ✅ | — | — | [GitHub](https://github.com/princeton-nlp/intercode) |
| 44 | WindowsAgentArena | 桌面(Win) | 154 | Azure VM | ✅ | ✅ | 19.5% (Navi) | [GitHub](https://github.com/microsoft/WindowsAgentArena) |
| 45 | OpsEval | IT运维知识 | 9,070 | ❌ | ✅ 80%隐藏 | 中 | — | [GitHub](https://github.com/NetManAIOps/OpsEval-Datasets) |

---

## 二、按赛道详细分析

### 赛道 1：代码修复 / 功能实现 / 重构

#### SWE-bench Live（微软）⭐⭐⭐ 首选

| 项目 | 详情 |
|------|------|
| 链接 | GitHub: https://github.com/microsoft/SWE-bench-Live / 排行榜: https://swe-bench-live.github.io/ |
| 论文 | NeurIPS 2025 D&B |
| 任务数 | ~1,890（持续增长，每月约+50） |
| 覆盖 | 223个仓库，多语言（Python/JS/Java/C++），多平台（Linux+Windows） |
| Docker | ✅ DockerHub 托管，命名 `starryzhang/sweb.eval.{platform}.{instance_name}` |
| 隐藏测试 | ✅ FAIL_TO_PASS + PASS_TO_PASS |
| 抗污染 | ✅ 强 — 仅收录 2024年1月后 issue |
| SOTA | ~50%（前沿模型） |
| 使用方式 | `pip install swebench` → Docker 拉取实例镜像 → `swebench evaluate` |
| 硬件需求 | x86_64，120GB+ 存储，16GB+ RAM |
| 推荐理由 | 滚动新增 + Docker成熟 + 多语言多平台，最接近"活的benchmark" |

#### SWE-bench Pro（Scale AI）⭐⭐⭐

| 项目 | 详情 |
|------|------|
| 链接 | GitHub: https://github.com/scaleapi/SWE-bench_Pro-os / 排行榜: https://labs.scale.com/leaderboard/swe_bench_pro_public |
| 论文 | arXiv:2509.16941（2025年9月） |
| 任务数 | 1,865（731公开 + 858 hold-out + 276商业） |
| 覆盖 | 41仓库，123种语言，copyleft + 私有商业仓库 |
| Docker | ✅ |
| 隐藏测试 | ✅（hold-out 分区） |
| 抗污染 | ✅ 强 — copyleft许可 + 商业仓库减少训练覆盖 |
| SOTA | ~23%（对比 Verified 的 72%，区分度极高） |
| 特点 | 平均修改 107.4行/4.1文件，所有任务至少需10行改动 |
| 使用方式 | 参照 SWE-bench 框架，公开部分可直接评测，hold-out 需提交到排行榜 |
| 推荐理由 | OpenAI 官方推荐的 Verified 替代品，前沿模型最有区分度 |

#### SWE-bench Original ⭐⭐（基线对照）

| 项目 | 详情 |
|------|------|
| 链接 | GitHub: https://github.com/SWE-bench/SWE-bench / HuggingFace: princeton-nlp/SWE-bench |
| 论文 | ICLR 2024 |
| 任务数 | 2,294（12个 Python 仓库） |
| Docker | ✅ 三层架构（Base → Env → Instance），约60个环境配置 |
| 隐藏测试 | ✅ test.patch 对 agent 不可见 |
| SOTA | ~55% |
| 已知问题 | 已被训练数据污染，31%弱测试，22.6%答案泄漏 |
| 使用方式 | `pip install swebench` → 构建 Docker 镜像 → `python -m swebench.harness.run_evaluation` |
| 推荐理由 | Docker 基础设施最成熟，文档最完善，适合做 10% 历史基线对照 |

#### SWE-bench Verified ❌ 不推荐

| 项目 | 详情 |
|------|------|
| 状态 | **2026年2月被 OpenAI 官方弃用** |
| 弃用原因 | 22.6%答案泄漏 + 59.4%缺陷/不可解 + 训练数据严重污染 |
| 参考 | [OpenAI声明](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/) |

#### SWE-rebench（Nebius）⭐⭐（大规模用）

| 项目 | 详情 |
|------|------|
| 链接 | HuggingFace: https://huggingface.co/datasets/nebius/SWE-rebench / 排行榜: https://swe-rebench.com/ |
| 任务数 | 21,000+ |
| Docker | ✅ |
| 特色 | 显式污染追踪（按模型发布日期标记），标准化 scaffolding |
| 使用方式 | HuggingFace datasets 加载，标准 SWE-bench 评估管线 |
| 推荐理由 | 大规模RL训练或大批量评估用 |

#### SWE-bench Multimodal ⭐（视觉补充）

| 项目 | 详情 |
|------|------|
| 链接 | 官网: https://www.swebench.com/multimodal.html / 论文: arXiv:2410.03859 |
| 任务数 | 617（17个 JavaScript 库） |
| Docker | ✅ |
| 特色 | Issue 描述含图片，测试视觉理解能力 |
| SOTA | <20%（现有 agent 表现差） |

#### BigCodeBench ⭐（函数级补充）

| 项目 | 详情 |
|------|------|
| 链接 | GitHub: https://github.com/bigcode-project/bigcodebench / 排行榜: https://bigcode-bench.github.io/ |
| 论文 | ICLR 2025，arXiv:2406.15877 |
| 任务数 | 1,140（每个5.6测试用例，99%分支覆盖）；BigCodeBench-Hard: 148 |
| Docker | ✅（v0.2.2） |
| SOTA | ~60%（人类97%） |
| 使用方式 | `pip install bigcodebench` → 生成代码 → 沙箱执行 → 评分 |

#### LiveCodeBench ⭐（滚动算法题）

| 项目 | 详情 |
|------|------|
| 链接 | GitHub: https://github.com/LiveCodeBench/LiveCodeBench / 排行榜: https://livecodebench.github.io/leaderboard.html |
| 论文 | arXiv:2403.07974 |
| 任务数 | 1,055+（v6，持续从 LeetCode/AtCoder/CodeForces 收集） |
| Docker | ✅ |
| 抗污染 | ✅ 按题目发布日期标注，可按模型截止日期过滤 |
| 使用方式 | `pip install livecodebench` → 按日期区间选题评估 |

#### Aider Polyglot ⭐（多语言参考）

| 项目 | 详情 |
|------|------|
| 链接 | 排行榜: https://aider.chat/docs/leaderboards/ / GitHub: https://github.com/Aider-AI/aider/blob/main/benchmark/README.md |
| 任务数 | 225（Exercism题，C++/Go/Java/JS/Python/Rust） |
| Docker | ❌ |
| SOTA | ~88%（Claude Opus 4.6），92.9%（Refact.ai+Claude 3.7） |
| 使用方式 | `aider --benchmark`，需配置目标 LLM API |
| 注意 | 测原始模型能力，不测 Agent 编排 |

---

### 赛道 2：ML Engineering / Kaggle++

#### MLE-bench（OpenAI）⭐⭐⭐ 首选

| 项目 | 详情 |
|------|------|
| 链接 | GitHub: https://github.com/openai/mle-bench / Blog: https://openai.com/index/mle-bench/ |
| 论文 | ICLR 2025 Oral，arXiv:2410.07095 |
| 任务数 | 75个 Kaggle 竞赛（测试集）+ 7个开发集 |
| 难度分布 | Low 22个(30%) / Medium 38个(50%) / High 15个(20%) |
| 领域 | 表格、CV、NLP、多模态、信号处理、序列数据 |
| Docker | ✅ 完整。`mlebench-env` 基础镜像（Ubuntu 20.04） |
| 资源限制 | 36 CPU / 440GB RAM / 1x A10 GPU(24GB) / 24小时时限 |
| 隐藏测试 | ✅ Kaggle held-out 测试集 |
| 评分 | 基于 Kaggle 公开排行榜的奖牌阈值（铜/银/金） |
| SOTA | 16.9% pass@1 / 34.1% pass@8（o1-preview + AIDE） |
| 使用方式 | 1. `pip install mle-bench` 2. 同意 Kaggle 条款下载数据 3. 构建 Docker 镜像 4. 配置 agent scaffolding 5. `mlebench run` |
| 硬件需求 | GPU 必需（A10 或同级），大存储 |
| 推荐理由 | 唯一要求完整 Kaggle 竞赛提交的 benchmark，工程完整性最高 |

#### DSBench ⭐⭐⭐

| 项目 | 详情 |
|------|------|
| 链接 | GitHub: https://github.com/LiqiangJing/DSBench |
| 论文 | ICLR 2025，arXiv:2409.07703 |
| 任务数 | 540（466数据分析 + 74数据建模） |
| Docker | ❌（需自行配置 Python 环境） |
| 评分 | 精确匹配 + RPG（数据分析）；Kaggle 排行榜式（数据建模） |
| SOTA | 34.12%（数据分析），RPG 34.74% |
| 使用方式 | 下载数据集 → 配置评估脚本 → 对接 agent |
| 推荐理由 | 覆盖分析+建模，与 MLE-bench 互补 |

#### MLAgentBench（Stanford）⭐⭐

| 项目 | 详情 |
|------|------|
| 链接 | GitHub: https://github.com/snap-stanford/MLAgentBench |
| 论文 | ICML 2024，arXiv:2310.03302 |
| 任务数 | 13个端到端 ML 实验 |
| Docker | 推荐（提供 Docker 镜像） |
| SOTA | 37.5%（Claude 3 Opus） |
| 使用方式 | Docker 运行 → agent 通过文件系统交互 → 自动评估 submission |
| 推荐理由 | 任务少但质量高，强调迭代实验 |

#### ScienceAgentBench ⭐⭐（科研方向）

| 项目 | 详情 |
|------|------|
| 链接 | GitHub: https://github.com/OSU-NLP-Group/ScienceAgentBench / 排行榜: https://hal.cs.princeton.edu/scienceagentbench |
| 论文 | ICLR 2025，arXiv:2410.05080 |
| 任务数 | 102（4学科/44论文） |
| 学科 | 生物信息学、计算化学、地理信息、心理学/认知神经 |
| Docker | ✅（2025.1发布，8线程30分钟跑完） |
| SOTA | 42.2%（o1-preview + self-debug） |
| 使用方式 | `pip install` → Docker 容器化评估 → 提交排行榜 |

---

### 赛道 3：终端真实工作流

#### Terminal-Bench 2.0 ⭐⭐⭐ 首选

| 项目 | 详情 |
|------|------|
| 链接 | GitHub: https://github.com/laude-institute/terminal-bench / 官网: https://www.tbench.ai/ / 排行榜: https://github.com/RDI-Foundation/terminal-bench-leaderboard |
| 论文 | arXiv:2601.11868 |
| 任务数 | 89（精心策划） |
| 16类任务 | Data-Processing, Data-Querying, Data-Science, Debugging, File-Operations, Games, Machine-Learning, Mathematics, Model-Training, Optimization, Personal-Assistant, Scientific-Computing, Security, Software-Engineering, System-Administration, Video-Processing |
| Docker | ✅ 每任务独立容器（Dockerfile + docker-compose.yaml），支持多容器场景 |
| 隐藏测试 | ✅ 测试在 agent 完成后才注入容器执行 |
| SOTA | 63%（Codex CLI + GPT-5.2）/ 58%（Terminus 2 + Claude Opus 4.5） |
| 使用方式 | 1. `pip install terminal-bench` 2. 需安装 `uv` 和 Docker 3. `terminal-bench run --agent <agent_name> --task <task_id>` |
| 集成难度 | **低** — 一条命令启动 |
| 推荐理由 | 前沿实验室标准评测，集成最简单 |

#### ITBench（IBM）⭐⭐⭐

| 项目 | 详情 |
|------|------|
| 链接 | GitHub: https://github.com/itbench-hub/ITBench / 排行榜: https://github.com/IBM/ITBench-Leaderboard / 轨迹: https://huggingface.co/datasets/ibm-research/ITBench-Trajectories |
| 论文 | ICML 2025 Oral，arXiv:2502.05352 |
| 任务数 | 102 |
| 三大领域 | SRE（K8s故障排查，11.4%）/ CISO（合规策略，25.2%）/ FinOps（成本异常，25.8%） |
| Docker | ✅ **K8s 沙箱集群**（最逼真的基础设施模拟） |
| 隐藏测试 | ✅ 预定义评估指标（MTTR/MTTA等） |
| 使用方式 | 需要 K8s 集群 → 部署场景 → agent 在容器中运行 → 自动评分 |
| 集成难度 | **中高** — 需要 K8s 环境 |
| 推荐理由 | 真实IT运维场景，SOTA极低说明难度很高 |

#### DevOps-Gym ⭐⭐（待确认）

| 项目 | 详情 |
|------|------|
| 论文 | ICLR 2026，arXiv:2601.20882 |
| 任务数 | 700+（30+ Java/Go 项目） |
| 分布 | Build 54 / Monitoring 34 / Issue 310 / Test 310 / E2E 18 |
| Docker | ✅ |
| 状态 | 论文已发但**代码开源状态未确认** |
| 关键发现 | Agent 在非Python语言表现显著下降 |

#### Cybench ⭐（安全补充）

| 项目 | 详情 |
|------|------|
| 链接 | GitHub: https://github.com/andyzorigin/cybench / 官网: https://cybench.github.io/ |
| 论文 | ICLR 2025，arXiv:2408.08926 |
| 任务数 | 40个CTF（密码学/Web安全/逆向/取证/pwn/杂项） |
| Docker | ✅ 每任务独立容器 |
| 难度 | 人类首解时间 2分钟 ~ 24小时54分钟 |
| 使用方式 | Docker 启动目标环境 → agent 交互 → 提交 flag |

---

### 赛道 4：Spreadsheet / BI / 商业分析

#### SpreadsheetBench ⭐⭐⭐ 首选

| 项目 | 详情 |
|------|------|
| 链接 | GitHub: https://github.com/RUCKBReasoning/SpreadsheetBench / HuggingFace: KAKA22/SpreadsheetBench |
| 论文 | NeurIPS 2024 D&B Spotlight，arXiv:2406.14991 |
| 任务数 | 912指令 / 2,729测试用例（平均每指令3个） |
| 来源 | 真实 Excel 论坛问题 |
| Docker | ✅（执行 LLM 生成的 Python 代码） |
| 隐藏测试 | ✅ 类OJ多IO对校验（结构相同、数据不同） |
| 使用方式 | 下载数据集 → LLM 生成 Python 代码 → Docker 中执行 → 与 ground truth spreadsheet 对比 |
| 还有 | SpreadsheetBench Verified 精选子集 |
| 推荐理由 | 任务量大 + Docker + 多测试用例，最适合自动评测 |

#### OfficeBench ⭐⭐

| 项目 | 详情 |
|------|------|
| 链接 | GitHub: https://github.com/zlwang-cs/OfficeBench |
| 论文 | arXiv:2407.19056 |
| 任务数 | 300（单应用93 + 双应用95 + 三应用112） |
| 覆盖 | Word + Excel + Calendar + Email 跨应用 |
| Docker | ✅（预装办公应用） |
| SOTA | 47%（GPT-4o） |
| 使用方式 | Docker 启动办公环境 → agent 执行跨应用操作 → 自动评估 |

#### OdysseyBench ⭐（待验证）

| 项目 | 详情 |
|------|------|
| 论文 | arXiv:2508.09124（2025） |
| 任务数 | 602（OdysseyBench+ 300真实 + Neo 302合成） |
| 覆盖 | Word, Excel, PDF, Email, Calendar |
| 状态 | 较新，需进一步验证开源和 Docker 支持情况 |

---

### 赛道 5：网页 / 数字员工任务

#### WebArena ⭐⭐⭐ 首选

| 项目 | 详情 |
|------|------|
| 链接 | GitHub: https://github.com/web-arena-x/webarena / Verified版: https://github.com/ServiceNow/webarena-verified |
| 论文 | ICLR 2024，arXiv:2307.13854 |
| 任务数 | 812（241模板，每模板3.3实例） |
| Docker | ✅ **6个独立容器**：Shopping(7770) + Admin(7780) + Reddit(9999) + GitLab(8023) + Map(3000) + Wikipedia(8888) |
| 自托管 | ✅ 完全自托管 |
| SOTA | ~35% |
| 使用方式 | 1. Docker Compose 启动6个网站 2. `pip install webarena-verified` 3. 配置 agent 通过 Playwright/Selenium 操作 4. 自动评估任务完成度 |
| 磁盘需求 | 30+GB（含完整网站数据） |
| 2026更新 | Docker 镜像体积缩小 92% |
| 推荐理由 | Web 赛道标杆，完全自托管，Docker 最成熟 |

#### TheAgentCompany ⭐⭐⭐

| 项目 | 详情 |
|------|------|
| 链接 | GitHub: https://github.com/TheAgentCompany/TheAgentCompany / 官网: https://the-agent-company.com/ |
| 论文 | arXiv:2412.14161（2024.12） |
| 任务数 | 175 |
| Docker | ✅ 多服务：**GitLab + Plane(项目管理) + RocketChat(IM) + ownCloud(文件)** + NPC同事 |
| 隐藏测试 | ✅ 加密评估脚本 + checkpoint-based 部分评分 |
| SOTA | 30.3% 完成 / 39.3% 部分完成（Gemini 2.5 Pro） |
| 使用方式 | Docker Compose 一键启动所有服务 → agent 在模拟企业环境中执行任务 → 自动评分 |
| 磁盘需求 | 30+GB |
| 推荐理由 | 最真实的企业SaaS环境，完美对标 require.md "自托管web environment" |

#### VisualWebArena ⭐⭐

| 项目 | 详情 |
|------|------|
| 链接 | GitHub: https://github.com/web-arena-x/visualwebarena |
| 论文 | arXiv:2401.13649 |
| 任务数 | 910（含人类轨迹） |
| Docker | ✅（基于 WebArena 扩展） |
| 特色 | 需要视觉理解（图像/图表/布局） |
| SOTA | ~20% |

#### OSWorld ⭐⭐（桌面级）

| 项目 | 详情 |
|------|------|
| 链接 | GitHub: https://github.com/xlang-ai/OSWorld / 官网: https://os-world.github.io/ |
| 论文 | NeurIPS 2024，arXiv:2404.07972 |
| 任务数 | 369 |
| 环境 | 真实OS（Ubuntu/Windows/macOS），通过 VM 运行 |
| SOTA | 12.24%（人类72.36%） |
| 使用方式 | 本地 VM 或 AWS 并行（AWS 1小时跑完） |
| 集成难度 | **较高** — 需要 VM 环境 |

#### GAIA ⭐⭐（通用助理）

| 项目 | 详情 |
|------|------|
| 链接 | HuggingFace: https://huggingface.co/datasets/gaia-benchmark/GAIA / 排行榜: https://hal.cs.princeton.edu/gaia |
| 论文 | ICLR 2024，arXiv:2311.12983 |
| 任务数 | 466（L1:146 / L2:245 / L3:75），公开165 + 隐藏~300 |
| Docker | ❌（agent 自配工具链） |
| 使用方式 | HuggingFace 下载 → agent 处理问题 → 提交答案到排行榜 |
| 注意 | ⚠️ 验证集答案已广泛流传，存在污染风险，只能依赖隐藏测试集 |

#### tau-bench ⭐（客服场景）

| 项目 | 详情 |
|------|------|
| 链接 | GitHub: https://github.com/sierra-research/tau-bench / v2: https://github.com/sierra-research/tau2-bench |
| 论文 | arXiv:2406.12045 |
| 任务数 | Airline 50 + Retail 114 + 扩展（Telecom, Mock） |
| Docker | ❌（纯Python，`uv sync`） |
| 特色 | 工具-Agent-用户三方交互，POMDP 隐藏意图 |
| 使用方式 | `uv sync` → Python 直接运行 → 自动评估 |

---

### 赛道 6：研究复现 / 科研生产

#### PaperBench（OpenAI）⭐⭐⭐ 首选

| 项目 | 详情 |
|------|------|
| 链接 | GitHub: https://github.com/openai/preparedness/tree/main/project/paperbench / Blog: https://openai.com/index/paperbench/ |
| 论文 | ICML 2025，arXiv:2504.01848 |
| 任务数 | 20篇 ICML 2024 Spotlight/Oral 论文 → **8,316个可独立评分的子任务** |
| Docker | ✅ **三容器隔离架构**：1. `agents/Dockerfile.base`（Agent运行） 2. `reproducer.Dockerfile`（GPU复现） 3. `grader.Dockerfile`（LLM评分） |
| 评分 | 层级式 Rubric（与论文原作者共同制定）→ LLM Judge 自动评分 |
| SOTA | 21-27%（Claude 3.5 Sonnet + 开源 scaffolding）；人类 ML PhD ~41% |
| 使用方式 | 1. 构建三个 Docker 镜像 2. Agent 在容器1中读论文写代码 3. 容器2执行复现 4. 容器3评分 |
| 硬件需求 | GPU 必需（复现阶段） |
| 变体 | PaperBench Code-Dev — 轻量版，跳过复现只评代码开发 |
| 推荐理由 | 最完整的"论文→代码→实验→评分"流程，非常适合文明沉淀 |

#### LMR-Bench ⭐⭐

| 项目 | 详情 |
|------|------|
| 链接 | GitHub: https://github.com/du-nlp-lab/LMR-Bench |
| 论文 | EMNLP 2025，arXiv:2506.17335 |
| 任务数 | 28个代码复现任务（23篇NLP论文，9个研究类别） |
| Docker | ✅ 隔离容器复现环境 |
| 验证 | 每个 masked 函数约3个严格单元测试 + LLM 正确性分类 |
| 推荐理由 | 与 PaperBench 互补，聚焦 NLP 领域代码复现 |

#### RE-Bench（METR）⭐⭐

| 项目 | 详情 |
|------|------|
| 链接 | GitHub: https://github.com/METR/RE-Bench |
| 论文 | arXiv:2411.15114（2024.11） |
| 任务数 | 7个开放式ML研究工程环境 + 71个人类专家8小时对照 |
| Docker | ✅ METR Task Standard |
| 任务类型 | Rust代码竞赛、LLM微调优化、GPU kernel优化（Triton）、Scaling law 预测 |
| 关键发现 | Agent 2小时内 = 人类4倍；但8小时后人类反超 |
| 推荐理由 | 测试 R&D 场景，短期爆发 vs 长期超越的发现对文明积累假说有启发 |

---

### 赛道 7：技能密集型生产力任务

> 目前无直接对标公开 benchmark，以下为可组合方案：

| 组合方案 | 任务数 | 覆盖场景 | 来源 |
|---------|--------|---------|------|
| OfficeBench | 300 | 跨应用办公交付（Word/Excel/Calendar/Email） | [GitHub](https://github.com/zlwang-cs/OfficeBench) |
| OdysseyBench | 602 | 复杂办公工作流（Word/Excel/PDF/Email/Calendar） | [arXiv](https://arxiv.org/abs/2508.09124) |
| SpreadsheetBench | 912 | 数据→洞察→决策建议 | [GitHub](https://github.com/RUCKBReasoning/SpreadsheetBench) |
| TheAgentCompany | 175 | 多角色SaaS协作 | [GitHub](https://github.com/TheAgentCompany/TheAgentCompany) |
| GAIA L2-3 | ~320 | 多步推理+工具使用+文件处理 | [HuggingFace](https://huggingface.co/datasets/gaia-benchmark/GAIA) |

**建议：** 这是 EpochX 最大的差异化机会。自建任务池覆盖"研究→内容→发布链"、"素材→成品"等场景，参考上述 benchmark 的 Docker + 多测试用例验证机制。

---

### 赛道 8（特殊）：文明观察层 — Skill 积累与复用

#### SkillsBench ⭐⭐⭐ 文明层核心

| 项目 | 详情 |
|------|------|
| 链接 | GitHub: https://github.com/benchflow-ai/skillsbench / 官网: https://www.skillsbench.ai/ |
| 论文 | arXiv:2602.12670（2026.2） |
| 任务数 | 84任务 / 11领域 |
| Skill 库 | **47,150 个唯一 Skill**（开源12,847 + Claude Code生态28,412 + 企业5,891） |
| 三种评估 | 无Skill / 人工策划Skill / 自生成Skill |
| Docker | ❌ |
| 核心数据 | 策划Skill平均 **+12.66pp**；医疗 +51.9pp；制造 +41.9pp；软件工程 +4.5pp |
| 轨迹数据 | 7,308条评估轨迹 |
| 使用方式 | 配置 agent + skill 库 → 在标准任务上测试有/无 skill 的表现差异 |
| 推荐理由 | **唯一直接验证 "Skill 让 Agent 变强" 假设的 benchmark**，与文明进化实验核心命题完美对标 |

---

### 补充：工具调用与函数调用

#### ToolBench ⭐⭐

| 项目 | 详情 |
|------|------|
| 链接 | GitHub: https://github.com/OpenBMB/ToolBench / 稳定版: https://github.com/THUNLP-MT/StableToolBench |
| 论文 | ICLR 2024 Spotlight |
| 规模 | 16,464 个真实 RESTful API，49个类别 |
| Docker | ❌ |
| 使用方式 | StableToolBench 提供 API 响应模拟，无需真实 API 调用 |
| 推荐理由 | 大规模工具调用评估，对标 AIP 协议和 Skill 组合调用 |

#### BFCL v4（Berkeley）⭐⭐

| 项目 | 详情 |
|------|------|
| 链接 | GitHub: https://github.com/ShishirPatil/gorilla/tree/main/berkeley-function-call-leaderboard / 排行榜: https://gorilla.cs.berkeley.edu/leaderboard.html |
| 论文 | ICML 2025 |
| 规模 | V2: ~1,435 / V3: +1,000多轮 / V4: +100多跳Web搜索 |
| Docker | ❌ |
| 评估 | AST 抽象语法树方法，串行/并行调用，多语言 |
| 使用方式 | Python 脚本直接评估，无需 Docker |
| 推荐理由 | 函数调用事实标准，Skill 调用本质就是函数调用 |

---

## 三、按维度快速筛选

### 需要 Docker 且环境成熟的（适合沙箱评测）

| Benchmark | Docker 成熟度 | 启动方式 |
|-----------|-------------|---------|
| Terminal-Bench 2.0 | ⭐⭐⭐ | `terminal-bench run` 一条命令 |
| SWE-bench Live | ⭐⭐⭐ | DockerHub 拉取 + `swebench evaluate` |
| SWE-bench Original | ⭐⭐⭐ | 三层镜像构建 + `run_evaluation` |
| WebArena | ⭐⭐⭐ | Docker Compose 启动6个网站 |
| TheAgentCompany | ⭐⭐⭐ | Docker Compose 启动多服务 |
| MLE-bench | ⭐⭐ | 构建 `mlebench-env` 镜像 + `mlebench run` |
| PaperBench | ⭐⭐ | 构建3个镜像（agent/reproducer/grader） |
| SpreadsheetBench | ⭐⭐ | Docker 执行生成代码 + 结果对比 |
| ITBench | ⭐⭐ | K8s 集群部署场景 |
| ScienceAgentBench | ⭐⭐ | Docker 容器化评估，8线程30分钟 |
| Cybench | ⭐⭐ | 每任务独立 Docker 容器 |

### 不需要 Docker 的（轻量评测）

| Benchmark | 使用方式 |
|-----------|---------|
| GAIA | HuggingFace 下载 + 提交排行榜 |
| Aider Polyglot | `aider --benchmark` |
| BFCL | Python 脚本评估 |
| tau-bench | `uv sync` + Python 运行 |
| SkillsBench | 配置 agent + skill 库 |
| CRUXEval | HuggingFace 下载 |
| ToolBench | StableToolBench 模拟 API |

### 抗污染能力最强的

| Benchmark | 抗污染机制 |
|-----------|-----------|
| SWE-bench Live | 仅收录2024.1后issue + 月增新题 |
| SWE-bench Pro | copyleft + 商业仓库 + hold-out |
| LiveCodeBench | 滚动收集竞赛新题 + 日期标注 |
| Terminal-Bench | 人工策划 + 后置隐藏验证 |
| PaperBench | 论文原作者rubric + LLM Judge |
| SWE-rebench | 显式污染追踪（按模型发布日期） |

### SOTA 最低 = 天花板最高、最有区分度

| Benchmark | SOTA | 人类基线 | 差距 |
|-----------|------|---------|------|
| ITBench (SRE) | 11.4% | — | 巨大空间 |
| OSWorld | 12.24% | 72.36% | 60pp |
| MLE-bench | 16.9% pass@1 | Kaggle铜牌线 | 巨大空间 |
| PaperBench | 21-27% | 41% (ML PhD) | 14-20pp |
| SWE-bench Pro | ~23% | — | 巨大空间 |
| TheAgentCompany | 30.3% | — | 巨大空间 |

---

## 四、关键参考文献与综述

| 类型 | 标题 | 链接 |
|------|------|------|
| 综述 | Evaluation and Benchmarking of LLM Agents: A Survey (KDD 2025) | [arXiv:2507.21504](https://arxiv.org/abs/2507.21504) |
| 综述 | Survey on Evaluation of LLM-based Agents (2025) | [arXiv:2503.16416](https://arxiv.org/abs/2503.16416) |
| 指南 | AI Coding Benchmarks 2026: Every Major Eval Explained | [MorphLLM](https://www.morphllm.com/ai-coding-benchmarks-2026) |
| 指南 | Top 50 AI Model Benchmarks & Evaluation Metrics (2025) | [o-mega.ai](https://o-mega.ai/articles/top-50-ai-model-evals-full-list-of-benchmarks-october-2025) |
| 指南 | 8 Benchmarks Shaping the Next Generation of AI Agents | [ainativedev.io](https://ainativedev.io/news/8-benchmarks-shaping-the-next-generation-of-ai-agents) |
| 弃用声明 | Why SWE-bench Verified No Longer Measures Frontier Coding | [OpenAI](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/) |
| 质量分析 | Many SWE-bench Passing PRs Would Not Be Merged | [METR](https://metr.org/notes/2026-03-10-many-swe-bench-passing-prs-would-not-be-merged-into-main/) |
| EvalPlus | HumanEval+ / MBPP+ 增强排行榜 | [evalplus.github.io](https://evalplus.github.io/leaderboard.html) |
| BrowserGym | Web Agent 统一评估框架（ServiceNow） | [GitHub](https://github.com/ServiceNow/BrowserGym) |

---

## 五、MVP 阶段推荐方案

### 第一阶段：Foundation Bench（门槛层，纯自动评测）

| 赛道 | Benchmark | 任务数 | 理由 |
|------|-----------|--------|------|
| 代码修复 | **SWE-bench Live** + Original(10%基线) | ~1,890+230 | 滚动抗污染 + Docker成熟 |
| 终端工作流 | **Terminal-Bench 2.0** | 89 | 一条命令启动，16类任务 |
| ML工程 | **MLE-bench** | 75竞赛 | 唯一完整 Kaggle Docker 环境 |

### 第二阶段：Rolling Arena（真实考验层）

| 赛道 | Benchmark | 任务数 | 理由 |
|------|-----------|--------|------|
| 代码(高难) | **SWE-bench Pro** | 1,865 | 最有区分度(23% SOTA) |
| 办公/BI | **SpreadsheetBench** | 912 | Docker+多测试用例 |
| Web/数字员工 | **WebArena** + **TheAgentCompany** | 812+175 | 完全自托管Docker |
| 科研复现 | **PaperBench** | 8,316子任务 | 三容器隔离，论文级复现 |

### 第三阶段：Civilization Layer（文明观察层）

| 维度 | Benchmark | 用途 |
|------|-----------|------|
| Skill增益验证 | **SkillsBench** | 直接测量 Skill 是否让 Agent 变强 |
| R&D能力对照 | **RE-Bench** | Agent vs 人类在研究任务的长短期对比 |
| 知识提取链 | **PaperBench + LMR-Bench** | 论文→代码→Skill 的完整链路 |
| 工具编排 | **BFCL v4 + ToolBench** | Skill 组合调用能力 |

---

## 六、风险提示

1. ❌ **SWE-bench Verified 已死** — 2026.2 被 OpenAI 弃用，绝不用作正式指标
2. ⚠️ **GAIA 验证集已污染** — 只能依赖隐藏测试集部分
3. ⚠️ **静态 benchmark 寿命约 12-18 个月** — 必须有滚动更新机制
4. ⚠️ **METR 研究发现**：约一半通过 SWE-bench 测试的 PR 实际上不会被维护者合并
5. ⏳ **DevOps-Gym 700+题** — ICLR 2026 但开源未确认，持续关注
6. ⏳ **TB-Science** — Q3 2026 才发布，可提前联系团队合作
7. ⚠️ **HumanEval/MBPP 已饱和** — 顶级模型 Pass@1 > 90%，不再有区分度
