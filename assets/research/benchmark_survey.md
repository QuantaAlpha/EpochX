# Agent Benchmark 全景调研

> 调研时间：2026-04-05
> 排除已列入 require.md 的：SWE-bench, Terminal-Bench, ITBench, MLE-bench, SpreadsheetBench, WebArena, VisualWebArena, TheAgentCompany, GAIA, PaperBench

---

## 一、代码修复 / 功能实现 / 重构

| Benchmark | 机构 / 会议 | 任务数 | 任务类型 | SOTA | SOTA 模型 | 需要 Docker | 使用方式 | 链接 |
|---|---|---|---|---|---|---|---|---|
| **FeatureBench** | ICLR 2026 | 200 任务，3825 环境 | 新功能开发（非 bug 修复），24 个真实开源仓库 | **11.0%** | Claude 4.5 Opus；GPT-5.1-Codex 12.5% | ✅ 每个任务有独立 Docker 环境 | 克隆 repo → 在 Docker 中执行 agent → hidden tests 自动评分 | [arXiv](https://arxiv.org/abs/2602.10975) · [GitHub](https://github.com/LiberCoders/FeatureBench) |
| **SWE-bench Pro** | Scale AI, ICLR | 1865 实例（731 公开 + 858 held-out + 276 商业） | 长链路多文件代码修改，41 个仓库 | **~45.9%**（最佳 scaffold 55.4%） | Claude Sonnet 4.5 + Live-SWE-agent | ✅ 标准 SWE-bench Docker 评测流程 | 与 SWE-bench 兼容，提交 patch → 隔离沙箱运行 hidden tests | [arXiv](https://arxiv.org/abs/2509.16941) · [Leaderboard](https://labs.scale.com/leaderboard/swe_bench_pro_public) · [Blog](https://scale.com/blog/swe-bench-pro) |
| **SWE-Compass** | 快手 KwaiPilot, 2025 | 2000 实例 | 8 任务类型 × 8 场景 × 10 语言（feature / refactor / config / perf 等） | 待公开完整排行 | SWE-Agent / Claude Code 框架评测 | ✅ GitHub PR 级别的 Docker 化评测 | 克隆 → agent 执行 → 自动评分 | [arXiv](https://arxiv.org/abs/2511.05459) · [GitHub](https://github.com/kwaipilot/SWE-Compass) |
| **SWE-PolyBench** | Amazon Science, 2025 | 2110 实例 | 多语言（Java 165 / JS 1017 / TS 729 / Python 199），21 仓库 | Python 最高，Java 最难（具体数值待查） | 多模型对比 | ✅ Docker 化评测 | 标准 SWE-bench 格式 + AST 评估指标 | [AWS Blog](https://aws.amazon.com/blogs/devops/amazon-introduces-swe-polybench-a-multi-lingual-benchmark-for-ai-coding-agents/) · [GitHub](https://github.com/amazon-science/SWE-PolyBench) · [HuggingFace](https://huggingface.co/datasets/AmazonScience/SWE-PolyBench) |
| **SWT-Bench** | LogicStar AI, NeurIPS 2024 | ~1600（Verified ~300） | 测试生成、测试修复、覆盖率提升 | 显著低于 SWE-bench patch 任务 | 多模型 | ✅ 与 SWE-bench 共享 Docker harness | 同 SWE-bench 流程，评估维度改为测试质量 | [Website](https://swtbench.com/) |
| **ProjDevBench** | 学术, 2026 | 20 | 从零构建完整项目：系统设计 + 代码实现 + 测试 + review | **27.38%** 整体接受率；执行通过率 77.85% | Codex / GPT-5 | ✅ 自动化评测环境 | 给定需求规格 → agent 从零开发 → 多维度评分（设计/执行/质量） | [arXiv](https://arxiv.org/abs/2602.01655) |
| **DPAI Arena** | JetBrains → Linux Foundation, 2025 | 140+ 任务（初始，持续扩展） | 多语言多工作流：patch / test gen / PR review / 静态分析 / repo 导航 | 平台型，无单一排行 | 多 agent 对比 | ✅ 标准化环境 | 社区贡献数据集 + 统一评测框架 | [Website](https://dpaia.dev/) · [JetBrains Blog](https://blog.jetbrains.com/blog/2025/10/28/introducing-developer-productivity-ai-arena-an-open-platform-for-ai-coding-agents-benchmarks/) |

### 评测时间与成本估算

| Benchmark | 环境搭建 | 单任务耗时 | 并行跑完全量（wall-clock） | 单任务 API 成本 | 全量 API 成本 | 额外基础设施成本 | 备注 |
|---|---|---|---|---|---|---|---|
| **FeatureBench** | 1-2h（Docker build × 24 repos） | 10-20 min | **4-6h**（8-16 并行容器） | $1-3 | **$200-600** | 无（本地可跑） | 每任务 Docker test timeout 180s |
| **SWE-bench Pro** | 2-4h（Docker 镜像 ~100GB+） | 10-30 min | **6-12h**（24 并行 worker，32 核机器） | ~$0.73 | **~$1,350** | 云 VM $50-100 | 参考 Epoch AI：32 核可在 62-73 min 跑完 SWE-bench Verified |
| **SWE-Compass** | 2-4h | 10-20 min | **8-16h**（16-24 并行） | $1-3 | **$2,000-6,000** | 无 | 2000 任务量大 |
| **SWE-PolyBench** | 2-4h | 10-20 min | **8-16h**（16-24 并行） | $1-3 | **$2,000-6,000** | 无 | 2110 任务，Java 任务更慢 |
| **SWT-Bench** | 1-2h | 3-5 min | Verified **1-3h** / 全量 **6-10h** | $0.50-1 | **$150-1,600** | 无 | Docker 环境搭建主导耗时 |
| **ProjDevBench** | 30 min | 30-60 min | **2-4h**（并行度受限，任务重） | $5-15 | **$100-300** | 无 | 仅 20 任务但单任务重 |
| **DPAI Arena** | 1-2h | 变化大 | **2-4h**（140+ 任务） | $1-3 | **$140-420** | 无 | 持续扩展中 |

---

## 二、终端 / DevOps / 系统运维

| Benchmark | 机构 / 会议 | 任务数 | 任务类型 | SOTA | SOTA 模型 | 需要 Docker | 使用方式 | 链接 |
|---|---|---|---|---|---|---|---|---|
| **DevOps-Gym** | 学术, 2026 | 700+ | build/config、监控、issue 修复、测试生成，Java + Go，30+ 项目 | 全面低分（所有 SOTA 模型） | 多模型 | ✅ 容器化 | 标准 gym 接口 → agent 在容器内执行 DevOps 操作 → 自动评分 | [arXiv](https://arxiv.org/abs/2601.20882) |
| **OSWorld** | XLANG Lab, NeurIPS 2024 | 369 | 真实 OS 环境（Ubuntu/Windows）：文件操作、浏览器、桌面应用、跨应用工作流 | **~76.3%**（超人类基线 72.4%） | Simular Agent S | ✅ VirtualBox VM + 程序化评测 | 启动 VM → agent 通过鼠标/键盘操作 → 状态检查评分 | [Website](https://os-world.github.io/) · [GitHub](https://github.com/xlang-ai/OSWorld) · [arXiv](https://arxiv.org/abs/2404.07972) |

### 评测时间与成本估算

| Benchmark | 环境搭建 | 单任务耗时 | 并行跑完全量（wall-clock） | 单任务 API 成本 | 全量 API 成本 | 额外基础设施成本 | 备注 |
|---|---|---|---|---|---|---|---|
| **DevOps-Gym** | 2-3h（Docker × 30+ 项目） | 5-15 min | **4-8h**（16+ 并行容器） | $0.50-2 | **$350-1,400** | 无 | 60s timeout + 3 retries / inference call |
| **OSWorld** | 2-4h（VM 镜像 + 应用配置） | 10-30 min（人类 ~2 min） | **3-6h**（AWS 支持 ~50 并行 VM） | $2-5（多模态截图重） | **$700-1,850** | 云 VM $50-200 | 截图密集，token 消耗大 |

---

## 三、ML 工程 / 科研复现

| Benchmark | 机构 / 会议 | 任务数 | 任务类型 | SOTA | SOTA 模型 | 需要 Docker | 使用方式 | 链接 |
|---|---|---|---|---|---|---|---|---|
| **RE-Bench** | METR, 2024 | 7 环境 | ML 研究工程：scaling laws / GPU kernel 优化 / 训练循环 | 2h 超人类 4x；**8h+ 被人类反超 2x** | Claude 3.5 / GPT-4o（61 位专家对比） | ✅ Docker 隔离环境 | 在 Docker 中给定 ML 任务 → agent 自由探索实验 → 按时间预算评分 | [METR Report](https://metr.org/AI_R_D_Evaluation_Report.pdf) · [Blog](https://metr.org/blog/2024-11-22-evaluating-r-d-capabilities-of-llms/) · [arXiv](https://arxiv.org/abs/2411.15114) |
| **ScienceAgentBench** | OSU NLP, ICLR 2025 | 102 | 4 学科 × 44 真实论文的计算实验复现 | **34.3%**（专家知识）；42.2%（o1 + self-debug） | o1-preview | ✅ 沙箱执行 | 给定论文 + 数据 → agent 编写代码复现实验 → 结果自动对比 | [Website](https://osu-nlp-group.github.io/ScienceAgentBench/) |
| **MLGym** | Meta AI, 2025 | 13 | CV / NLP / RL / 博弈论的开放式 ML 研究任务 | AUP@4: 1.029-1.176 | o1-preview | ✅ Docker 安全工作区 | Gym 接口 → agent 在容器内迭代实验 → 按改进幅度评分 | [arXiv](https://arxiv.org/abs/2502.14499) |
| **CORE-Bench** | Princeton, 2024 | 270（90 篇论文 × 3 难度） | CS / 社科 / 医学论文的计算可复现性 | **Hard: 19%**（原始）；近期 Claude Code scaffold 显著提升 | Claude Code | ✅ Docker 执行 | 给定论文 repo → agent 尝试复现 → 输出与参考对比 | [Website](https://hal.cs.princeton.edu/corebench_hard) |
| **FrontierScience** | OpenAI, 2025 | 未公开具体数 | 物理/化学/生物：Olympiad（定义明确）+ Research（开放式科研推理） | Olympiad 77% / **Research 25%** | GPT-5.2 | ❌ API 调用评测 | 提交答案 → 自动评分（Olympiad）/ 专家评分（Research） | [OpenAI Blog](https://openai.com/index/frontierscience/) |

### 评测时间与成本估算

| Benchmark | 环境搭建 | 单任务耗时 | 并行跑完全量（wall-clock） | 单任务 API 成本 | 全量 API 成本 | 额外基础设施成本 | 备注 |
|---|---|---|---|---|---|---|---|
| **RE-Bench** | 1-2h（Docker + 最多 6× H100 GPU / 环境） | 2h 或 8h 时间预算 / 环境 | **16-56h**（7 环境串行，GPU 限制并行度） | $70-300 / 环境 | **$500-2,000+** | **H100 GPU 租用 ~$2-3/hr/GPU，主要成本** | 所有 benchmark 中 GPU 需求最高 |
| **ScienceAgentBench** | 30 min - 1h | 2-5 min | **~30 min**（8 线程并行，论文确认） | $0.50-2 | **$50-200** | 无 | 最轻量的科研基准之一 |
| **MLGym** | 1-2h（Docker/Podman） | 2h 预算 / 任务（可配置），$4 上限 | **4-8h**（部分可并行） | ~$4 cap | **~$52** | 部分任务需 GPU 做训练 | 成本上限设计友好 |
| **CORE-Bench** | 2-3h（Docker / Azure VM） | 5-20 min（按难度） | **4-8h**（并行 Docker 容器） | $1-3 | **$270-810** | 无 | 难度分 Easy/Medium/Hard |
| **FrontierScience** | 30 min | 5-15 min | **2-4h**（并行 API） | $1-5 | **$200-1,000**（估） | 无 | 数据集非完全公开 |

---

## 四、数据分析 / 表格 / 商业智能

| Benchmark | 机构 / 会议 | 任务数 | 任务类型 | SOTA | SOTA 模型 | 需要 Docker | 使用方式 | 链接 |
|---|---|---|---|---|---|---|---|---|
| **DABstep** | Adyen + HuggingFace, 2025 | 450+ | 真实金融分析：多步数据处理、异构文档交叉引用、精确报告 | **Hard: 14.55%** | o3-mini / DeepSeek-R1 (~13-16%) | ❌ 代码执行评测（可加沙箱） | 给定数据 + 问题 → agent 编写代码分析 → 精确值自动比对 | [HuggingFace](https://huggingface.co/blog/dabstep) · [arXiv](https://arxiv.org/abs/2506.23719) |
| **DA-Code** | EMNLP 2024 | 500 | 数据科学代码生成：数据清洗、ML pipeline、EDA | **38.5%** | Google DS-STAR | ✅ 沙箱代码执行 | 给定数据文件 + 任务描述 → agent 生成代码 → 执行验证 | [Website](https://da-code-bench.github.io/) |
| **DataSciBench** | 清华 THUDM, 2025 | ~100-300 | 全数据科学生命周期：清洗 → 探索 → 可视化 → 建模 | **66.31%** | GPT-4o | ✅ 执行评测 | 标准化数据科学任务 → 代码执行 → 自动评分 | [Website](https://datascibench.github.io/) |
| **OdysseyBench** | 学术, 2025 | 602（300 真实 + 302 合成） | Word / Excel / PDF / Email / Calendar 长链路办公工作流 | 待公开 | 多模型 | ❌ 桌面应用模拟 | 给定办公场景 → agent 操作多个办公应用 → 状态检查评分 | [arXiv](https://arxiv.org/abs/2508.09124) |

### 评测时间与成本估算

| Benchmark | 环境搭建 | 单任务耗时 | 并行跑完全量（wall-clock） | 单任务 API 成本 | 全量 API 成本 | 额外基础设施成本 | 备注 |
|---|---|---|---|---|---|---|---|
| **DABstep** | 30 min（HuggingFace 数据集下载 + Python 环境） | 3-10 min | **3-6h**（可并行） | $0.50-2 | **$225-900** | 无 | Hard 子集可单独跑 |
| **DA-Code** | 1h（数据下载 + 可执行环境） | 5-15 min（每任务最多 20 步） | **4-8h**（可并行） | $0.50-2 | **$250-1,000** | 无 | |
| **DataSciBench** | 30 min - 1h | 3-10 min | **2-4h** | $0.50-1 | **$50-300** | 无 | |
| **OdysseyBench** | 1-2h（桌面应用模拟配置） | 10-30 min | **6-12h** | $2-5 | **$1,200-3,000**（估） | 桌面环境模拟 | 长链路任务，单任务较重 |

---

## 五、网页 / 企业 SaaS / 数字员工

| Benchmark | 机构 / 会议 | 任务数 | 任务类型 | SOTA | SOTA 模型 | 需要 Docker | 使用方式 | 链接 |
|---|---|---|---|---|---|---|---|---|
| **WorkArena++ (L2)** | ServiceNow, NeurIPS 2024 | 682 组合任务 | 真实 ServiceNow 企业界面：表单填写、多步工作流、数据库交互 | **L2: 39.1%**；GPT-4o 仅 8.5% | Claude 3.5 Sonnet | ✅ BrowserGym + Playwright | BrowserGym 框架启动 → agent 通过浏览器 API 操作 → 自动评分 | [Website](https://servicenow.github.io/WorkArena/) · [GitHub (BrowserGym)](https://github.com/ServiceNow/BrowserGym) |
| **AppWorld** | ACL 2024 最佳资源论文 | 750 | 9 个 App × 457 API 的链式调用：跨应用数据处理、状态维护 | Normal 49% / **Challenge 30%** | GPT-4o; CUGA 73.2% normal | ✅ 60K 行执行环境代码 | 安装 AppWorld → agent 通过 API 完成任务 → 自动验证 | [Website](https://appworld.dev/) · [arXiv](https://arxiv.org/abs/2407.18901) |
| **SCUBA** | Salesforce AI Research, 2025 | 300 | 真实 CRM 工作流（管理员/销售/客服 3 种角色） | **闭源最佳 39%**；开源 <5%；加演示最高 50% | 闭源模型 | ✅ Salesforce 模拟环境 | 启动 CRM 模拟 → agent 操作界面 → 评分含延迟/成本/步数 | [Website](https://sfrcua.github.io/SCUBA/) · [GitHub](https://github.com/SalesforceAIResearch/SCUBA) · [arXiv](https://arxiv.org/abs/2509.26506) |
| **CUB** | Theta Software, 2025 | 106 工作流 × 7 行业 | 消费/建筑/金融/医疗/营销/销售/供应链的端到端计算机操作 | **10.4%** | Writer's Action Agent | ✅ 评测环境 | 给定行业场景 → agent 操作桌面/网页 → 工作流状态检查 | [Blog](https://thetasoftware.com/blog/introducing-cub/) |
| **UI-CUBE** | UiPath, 2025 | 226（2 难度层） | 企业 UI 适配与工作流协调，测部署就绪度 | 人类 61.2%（复杂任务），**Agent 远低于** | 多模型 | ✅ 评测框架 | 标准化 UI 任务 → agent 执行 → 测可靠性（非仅准确率） | [Website](https://www.uipath.com/ai/research/ui-cube-benchmark) · [arXiv](https://arxiv.org/abs/2511.17131) |
| **BrowserGym** | ServiceNow, ICLR 2025 | 聚合平台 | 统一多个 Web 基准（WorkArena / WebArena / MiniWoB++） | 随子基准变化 | -- | ✅ Playwright | `pip install browsergym` → 统一 API 调用各子基准 | [GitHub](https://github.com/ServiceNow/BrowserGym) |
| **MobileWorld** | 学术, 2025 | 201 × 20 真实 App | Android 移动端自动化（AndroidWorld 后继，更难） | **框架 51.7%** / 端到端模型 20.9% | 最佳 agentic 框架 | ✅ Android 模拟器 | 启动模拟器 → agent 操作移动 UI → 状态校验 | [arXiv](https://arxiv.org/abs/2512.19432) |

### 评测时间与成本估算

| Benchmark | 环境搭建 | 单任务耗时 | 并行跑完全量（wall-clock） | 单任务 API 成本 | 全量 API 成本 | 额外基础设施成本 | 备注 |
|---|---|---|---|---|---|---|---|
| **WorkArena++ (L2)** | 2-4h（ServiceNow 实例 + BrowserGym） | 10-30 min | **8-16h**（并行浏览器受 ServiceNow API 限制） | $2-5 | **$1,360-3,410** | ServiceNow 实例费用 | 企业 SaaS 实例是瓶颈 |
| **AppWorld** | 1-2h（9 App + 457 API + 数据库初始化） | 5-15 min（常需 15+ API、80+ 行代码） | **6-12h**（可并行） | $1-3 | **$750-2,250** | 无 | |
| **SCUBA** | 2-4h（Salesforce 沙箱环境） | 10-20 min | **4-8h**（支持并行） | $2-5 | **$600-1,500** | Salesforce 沙箱费用 | |
| **CUB** | 2-3h（浏览器环境 × 7 行业） | 10-30 min | **3-6h** | $2-5 | **$210-530** | 无 | |
| **UI-CUBE** | 1-2h | 5-20 min | **3-6h** | $2-5 | **$450-1,130** | 无 | |
| **BrowserGym** | 1h（pip install + 配置子基准） | 随子基准 | 随子基准 | 随子基准 | 随子基准 | 无 | 聚合框架 |
| **MobileWorld** | 3-5h（Docker-in-Docker + Android AVD + App 后端） | 15-30 min（平均 27.8 步，最多 50 步） | **4-8h**（并行 AVD 实例） | $2-5 | **$400-1,000** | 云 AVD 计算 $50-150 | 搭建最复杂 |

---

## 六、网络安全

| Benchmark | 机构 / 会议 | 任务数 | 任务类型 | SOTA | SOTA 模型 | 需要 Docker | 使用方式 | 链接 |
|---|---|---|---|---|---|---|---|---|
| **Cybench** | 多机构, ICLR 2025 | 40 | 专业级 CTF：密码学 / Web 安全 / 逆向 / 取证 / 漏洞利用 | **~46%** | Claude Sonnet 4.5 | ✅ Docker (Kali Linux) + K8s | 启动 CTF 容器 → agent 自由探索攻击 → flag 提交验证 | [Website](https://cybench.github.io/) |
| **CAIBench** | 学术, 2025 | 10000+ 实例 | 元基准：Jeopardy CTF / 攻防 CTF / Cyber Range / 知识 / 隐私 | 各模块差异大 | 多模型 | ✅ 模块化环境 | 选择评估模块 → 在对应环境中执行 → 分模块评分 | [arXiv](https://arxiv.org/abs/2510.24317) |
| **CTFusion** | 学术, 2025 | 实时竞赛 | 使用真实 live CTF 竞赛进行流式评测，避免数据污染 | 持续更新 | -- | ✅ 虚拟化隔离 | 接入实时 CTF → agent 独立参赛 → 实时评分 | [OpenReview](https://openreview.net/forum?id=2zQJHLbyqM) |

### 评测时间与成本估算

| Benchmark | 环境搭建 | 单任务耗时 | 并行跑完全量（wall-clock） | 单任务 API 成本 | 全量 API 成本 | 额外基础设施成本 | 备注 |
|---|---|---|---|---|---|---|---|
| **Cybench** | 1-2h（Kali Linux Docker 镜像 + 任务服务器） | 高度不均：简单 5-15 min，难题 1-2h（人类首次解题 2 min ~ 24h54m） | **4-10h**（并行度受限；bash/python 180s timeout × 3 attempts） | $2-10 | **$80-400** | 无 | 难题方差极大 |
| **CAIBench** | 2-4h（模块化，按需配置） | 变化大 | **10-30h**（10000+ 实例，需按模块分批） | $0.10-5 | **$1,000-5,000**（估） | 可能需 Cyber Range 基础设施 | 规模最大 |
| **CTFusion** | 1-2h | 取决于竞赛 | 取决于竞赛时长 | 变化大 | 变化大 | 无 | 实时竞赛制 |

---

## 七、专业白领 / 技能密集型生产力

| Benchmark | 机构 / 会议 | 任务数 | 任务类型 | SOTA | SOTA 模型 | 需要 Docker | 使用方式 | 链接 |
|---|---|---|---|---|---|---|---|---|
| **APEX-Agents** | Mercor, 2026 | 400（100/领域 × 4） | 投行分析 / 管理咨询 / 大型律所 / 初级医疗，平均 26K token 源文档 | **24.0%** | Gemini 3 Flash Thinking=High | ❌ 纯文本推理 + 人工评分 | 下载数据集 → agent 处理文档并输出专业交付物 → rubric 评分 | [Website](https://www.mercor.com/apex/) · [arXiv](https://arxiv.org/abs/2601.14242) · [HuggingFace](https://huggingface.co/datasets/mercor/apex-agents) |

### 评测时间与成本估算

| Benchmark | 环境搭建 | 单任务耗时 | 并行跑完全量（wall-clock） | 单任务 API 成本 | 全量 API 成本 | 额外基础设施成本 | 备注 |
|---|---|---|---|---|---|---|---|
| **APEX-Agents** | 1-2h（文档加载，~26K token/case） | 5-15 min / run；每任务跑 8 次取统计稳健性 | **8-16h**（400 × 8 = 3200 次评测） | $1-3 / run | **$3,200-9,600**（含 8 runs + Judge LM 评分） | 无 | 成本较高，因为需多次重复 + LLM-as-Judge |

---

## 八、工具使用 / Agent 可靠性

| Benchmark | 机构 / 会议 | 任务数 | 任务类型 | SOTA | SOTA 模型 | 需要 Docker | 使用方式 | 链接 |
|---|---|---|---|---|---|---|---|---|
| **tau-bench / tau2-bench** | Sierra AI, 2024-2025 | 多领域（零售/航空/电信/银行） | 工具-Agent-用户交互：策略遵守、工具调用、一致性 | Retail 74% / **Airline 56%** / pass^8 <25% | GPT-4.1 / Claude 3.7 | ❌ 模拟 API 环境 | 运行模拟 → agent 处理用户请求 → 按 pass^k 一致性评分 | [GitHub](https://github.com/sierra-research/tau-bench) |
| **BFCL v4** | UC Berkeley Gorilla, 2024-2025 | 4951 | 函数调用：串行/并行/多轮/多步，Python/Java/JS/SQL/REST | 简单 ~90%，**复杂/agentic 显著低** | 各模型各有优势 | ❌ API 评测 | 标准化输入 → 模型输出函数调用 → AST 对比评分 | [Leaderboard](https://gorilla.cs.berkeley.edu/leaderboard.html) · [GitHub](https://github.com/ShishirPatil/gorilla/tree/main/berkeley-function-call-leaderboard) |

### 评测时间与成本估算

| Benchmark | 环境搭建 | 单任务耗时 | 并行跑完全量（wall-clock） | 单任务 API 成本 | 全量 API 成本 | 额外基础设施成本 | 备注 |
|---|---|---|---|---|---|---|---|
| **tau-bench** | 30 min（Python 环境 + 模拟配置） | 1-3 min（$0.086 agent + $0.059 user 模拟 / 任务） | **1-3h** | ~$0.14 | **~$40 / trial**（论文确认）；pass^5 需 5 trials → **~$200** | 无 | 所有基准中性价比最高之一 |
| **BFCL v4** | 30 min - 1h（Python + API keys） | 5-30 秒（函数调用，非多步 agentic） | **1-3h**（主要是 API 延迟） | <$0.01 | **$5-50** | 无 | 最便宜的基准 |

---

## 九、通用推理 / 抽象能力

| Benchmark | 机构 / 会议 | 任务数 | 任务类型 | SOTA | SOTA 模型 | 需要 Docker | 使用方式 | 链接 |
|---|---|---|---|---|---|---|---|---|
| **ARC-AGI-2** | ARC Prize Foundation, 2025 | ~400 训练 + 100 eval + 240 私有 | 抽象推理：程序化生成的视觉模式泛化，人类 <=2 次尝试可解 | **竞赛 ~24%**；Poetiq ~50%（半私有集） | NVARC（竞赛）/ Poetiq（eval） | ❌ 纯推理 | 输入 grid → 输出 grid → 精确匹配 | [Website](https://arcprize.org/arc-agi/2) · [arXiv](https://arxiv.org/abs/2601.10904) · [Results](https://arcprize.org/blog/arc-prize-2025-results-analysis) |
| **Humanity's Last Exam** | CAIS + Scale AI, Nature 2025 | 2500 | 100+ 学科专家级知识（数学 41% / 生物 11% / CS 10% / 物理 9%） | **48.1%**（带工具）/ 41.6%（无工具） | Zoom AI（带工具）/ GPT-5.4 | ❌ API 评测 | 提交答案 → 精确匹配评分 | [Website](https://agi.safe.ai/) · [arXiv](https://arxiv.org/abs/2501.14249) · [Leaderboard](https://labs.scale.com/leaderboard/humanitys_last_exam) · [Nature](https://www.nature.com/articles/s41586-025-09962-4) |
| **FrontierMath** | Epoch AI, 2024-2026 | 350（T1-T4）+ Open Problems | 本科到研究级数学推理，Open Problems 为人类未解问题 | T1-3 ~50% / **T4 ~38%** / Open ~0% | GPT-5.4 Pro | ❌ 纯推理 | 提交数学答案 → 精确数值比对 | [Website](https://epoch.ai/frontiermath/) · [arXiv](https://arxiv.org/abs/2411.04872) · [Tier 4](https://epoch.ai/benchmarks/frontiermath-tier-4) |
| **BALROG** | ICLR 2025 | 多环境 | 长时程游戏推理：NetHack / BabyAI / Crafter 等 | 复杂环境**极低**（远低于 RL agent） | GPT-4o / Claude 3.5 | ❌ 游戏模拟器 | 安装游戏环境 → agent 文本/视觉交互 → 按游戏进度评分 | [Website](https://balrogai.com/) · [arXiv](https://arxiv.org/abs/2411.13543) |

### 评测时间与成本估算

| Benchmark | 环境搭建 | 单任务耗时 | 并行跑完全量（wall-clock） | 单任务 API 成本 | 全量 API 成本 | 额外基础设施成本 | 备注 |
|---|---|---|---|---|---|---|---|
| **ARC-AGI-2** | 30 min | 高度依赖方法：高效 $0.20/task；暴力深度思考 $30-77/task | **2-24h**（取决于方法和计算预算） | $0.20-77 | **$80-30,000+**（方法差异 100x+） | 无 | 成本方差最大的基准 |
| **Humanity's Last Exam** | 30 min（数据集下载 + API 配置） | 2-5 min（推理模型最少 8K completion tokens） | **4-10h**（可并行 API 调用） | ~$3 | **~$7,500** | 无 | 成本主要来自 reasoning token |
| **FrontierMath** | 30 min（需向 Epoch AI 申请私有数据集访问权限） | 5-30 min（10K+ token 预算，部分需脚本执行） | **4-12h** | $2-10 | **$700-3,500** | 无 | 需申请数据集权限 |
| **BALROG** | 1-2h（游戏环境安装） | 数分钟到数小时（NetHack 极长） | **6-24h**（视环境） | $1-20 | **$500-5,000**（估） | 无 | NetHack 环境最耗时 |

---

## 十、多 Agent 协作

| Benchmark | 机构 / 会议 | 任务数 | 任务类型 | SOTA | SOTA 模型 | 需要 Docker | 使用方式 | 链接 |
|---|---|---|---|---|---|---|---|---|
| **MultiAgentBench** | ACL 2025 | 多场景 | 协作与竞争：星形/链式/树形/图拓扑，里程碑 KPI | 架构间差异显著 | 多模型 | ❌ 模拟环境 | 配置拓扑 → 多 agent 交互 → milestone KPI 评分 | [ACL](https://aclanthology.org/2025.acl-long.421/) · [arXiv](https://arxiv.org/abs/2503.01935) |
| **COMMA** | 学术, 2024-2025 | 多模态拼图 | 多模态多 Agent 沟通协作 | **效率 0.52**（人类 0.78） | GPT-4o | ❌ 模拟环境 | 多 agent 通过语言沟通完成拼图 → 效率评分 | [GitHub](https://github.com/tossowski/COMMA) · [arXiv](https://arxiv.org/abs/2410.07553) |

### 评测时间与成本估算

| Benchmark | 环境搭建 | 单任务耗时 | 并行跑完全量（wall-clock） | 单任务 API 成本 | 全量 API 成本 | 额外基础设施成本 | 备注 |
|---|---|---|---|---|---|---|---|
| **MultiAgentBench** | 1h | 5-20 min（多 agent 交互轮次多） | **3-8h** | $2-10（多 agent 多轮对话） | **$500-2,000**（估） | 无 | 成本随 agent 数量线性增长 |
| **COMMA** | 30 min | 3-10 min | **1-3h** | $1-5 | **$200-500**（估） | 无 | |

---

## 十一、其他值得关注

| Benchmark | 机构 | 任务类型 | SOTA | 需要 Docker | 链接 |
|---|---|---|---|---|---|
| **AgentBench** | 清华 THUDM, ICLR 2024 | 8 类环境（OS / DB / 知识图谱 / 卡牌 / 购物 / 浏览 / 家务等） | 商业模型远超开源 | ✅ 每环境有 Docker 镜像 | [GitHub](https://github.com/THUDM/AgentBench) |
| **SafeAgentBench** | 学术, 2024 | 安全感知任务规划（750 任务 × 10 危害类别） | 安全任务 69% / **危险拒绝率仅 5%** | ❌ 模拟 | [Website](https://safeagentbench.github.io/) · [arXiv](https://arxiv.org/abs/2412.13178) |
| **AI-Trader** | HKUDS, 2025 | 实时交易：美股/A股/加密货币 | 通用智能 ≠ 交易能力 | ❌ 实时行情 API | [GitHub](https://github.com/HKUDS/AI-Trader) · [arXiv](https://arxiv.org/abs/2512.10971) |
| **LoCoMo** | Snap Research, 2024-2026 | 300 轮多会话长期记忆（事实回忆/时序/因果） | **GPT-4: 32.1 F1**（人类 87.9） | ❌ API 评测 | [Website](https://snap-research.github.io/locomo/) · [GitHub](https://github.com/snap-research/locomo) · [arXiv](https://arxiv.org/abs/2402.17753) |
| **LiveBench** | ICLR 2025 Spotlight | 18 任务 × 6 类（每月更新抗污染） | 顶尖模型 <70% | ❌ API 评测 | [Website](https://livebench.ai/) · [GitHub](https://github.com/LiveBench/LiveBench) |
| **AgentArch** | ServiceNow, 2025 | 测 18 种 agent 架构选择（非模型能力） | **复杂企业任务 35.3%** | ✅ | [GitHub](https://github.com/ServiceNow/AgentArch) · [arXiv](https://arxiv.org/abs/2509.10769) |
| **METR 时间地平线** | METR, 2025 | 按任务持续时间衡量 agent 能力（~7 月翻倍） | Claude 3.7: 50% 时间地平线 ~50 分钟 | ✅ | [Blog](https://metr.org/blog/2025-03-19-measuring-ai-ability-to-complete-long-tasks/) · [arXiv](https://arxiv.org/abs/2503.14499) |

### 评测时间与成本估算

| Benchmark | 环境搭建 | 并行跑完全量（wall-clock） | 全量 API 成本 | 备注 |
|---|---|---|---|---|
| **AgentBench** | 2-3h（8 类 Docker 环境） | 4-8h | $500-1,500 | 8 环境各自独立 |
| **SafeAgentBench** | 30 min | 2-4h | $200-500 | |
| **AI-Trader** | 1h | 取决于回测时段 | 变化大 | 实时数据 API 可能收费 |
| **LoCoMo** | 30 min | 2-4h | $100-300 | |
| **LiveBench** | 30 min | 2-4h | $100-500 | 每月更新 |
| **AgentArch** | 2-3h | 4-8h | $500-2,000 | 18 种架构 × 6 模型 |
| **METR 时间地平线** | 1-2h | 8-24h | $500-2,000 | 长时任务定义 |

---

## 影响力排行（全部 Benchmark）

> **排序依据**：GitHub Star 数、HuggingFace 下载量、Semantic Scholar 引用数、顶会收录、主流媒体报道频次等综合评估。数据采集时间：2026-04-05。

### Tier 1 — 行业标杆（⭐ 3000+ 或引用 400+）

| 排名 | Benchmark | 赛道 | ⭐ GitHub Stars | 📚 引用数 | 📦 HF 下载 | 🏛️ 顶会/媒体 | 影响力说明 |
|---|---|---|---|---|---|---|---|
| 1 | **BFCL v4 (Gorilla)** | 工具调用 | **12,797** | — | 71K | ICML 2025 | 函数调用评测事实标准，star 数遥遥领先 |
| 2 | **ARC-AGI-2** | 抽象推理 | **4,739** | 98 | — | Nature, Time, Forbes, TechCrunch | $1M 大奖赛，4 家顶级实验室在 model card 中汇报成绩 |
| 3 | **AgentBench** | 综合 Agent | **3,299** | **659** | — | ICLR 2024 | 首个 LLM-as-Agent 综合基准，开山之作 |
| 4 | **OSWorld** | 桌面 OS | **2,736** | **530** | 546K | NeurIPS 2024 | 真实 OS 环境基准标杆，引用量 Agent 方向第二 |

### Tier 2 — 主流影响力（⭐ 1000+ 或引用 100+）

| 排名 | Benchmark | 赛道 | ⭐ GitHub Stars | 📚 引用数 | 📦 HF 下载 | 🏛️ 顶会/媒体 | 影响力说明 |
|---|---|---|---|---|---|---|---|
| 5 | **Humanity's Last Exam** | 专家推理 | 1,469 | **308** | 45K | **Nature 2025** | 登 Nature 正刊，2500 学科人类最难题 |
| 6 | **tau-bench** | 工具可靠性 | 1,160 | **437** | — | Sierra AI | 引用量极高，pass^k 指标被广泛采纳 |
| 7 | **BrowserGym / WorkArena++** | 网页/企业 SaaS | **1,428** (合计) | 161 | — | TMLR 2025 / NeurIPS 2024 | ServiceNow 出品，Web Agent 统一评测框架 |
| 8 | **LoCoMo** | 长期记忆 | 714 | **329** | — | ACL 2024 | 长期记忆评测标准，Snap Research 出品 |
| 9 | **LiveBench** | 通用推理 | 1,122 | 102 | — | ICLR 2025 Spotlight | 月更抗数据污染，社区活跃度高 |
| 10 | **SWE-bench Pro** | 代码 | 334 | 55 | **834K** | Scale AI | HF 下载量最高，有独立 Leaderboard |
| 11 | **FrontierMath** | 数学推理 | — | **156** | — | Epoch AI; TechCrunch, IEEE | 人类未解数学题，引用增长快 |
| 12 | **AppWorld** | 网页/API | 401 | **120** | — | **ACL 2024 最佳资源论文** | 顶会最佳论文奖，学术认可最高之一 |
| 13 | **SWT-Bench** | 测试生成 | 76 | **100** | — | NeurIPS 2024 | SWE-bench 姊妹基准，测试方向标准 |

### Tier 3 — 快速增长（⭐ 100+ 或引用 50+）

| 排名 | Benchmark | 赛道 | ⭐ GitHub Stars | 📚 引用数 | 📦 HF 下载 | 🏛️ 顶会/媒体 | 影响力说明 |
|---|---|---|---|---|---|---|---|
| 14 | **BALROG** | 游戏推理 | 242 | 84 | — | ICLR 2025 | 长时程博弈推理，NVIDIA 博客推荐 |
| 15 | **Cybench** | 网络安全 | 217 | 83 | — | ICLR 2025 | 被 US/UK AISI 用于前沿模型安全评估 |
| 16 | **MultiAgentBench** | 多 Agent | 244 | 78 | — | ACL 2025 | 多 Agent 协作评测新标准 |
| 17 | **RE-Bench** | ML R&D | 134 | 76 | — | METR | "最有影响力的 AI 进步评估"，安全评估核心 |
| 18 | **ScienceAgentBench** | 科研复现 | 133 | 46-71 | — | ICLR 2025 | 轻量科研基准，跑完仅 30 min |
| 19 | **SafeAgentBench** | 安全 | 68 | 63 | — | — | Agent 安全意识评测 |
| 20 | **MLGym** | ML 研究 | 594 | 57 | — | Meta AI | Meta 出品，star 数高但论文引用追赶中 |
| 21 | **CORE-Bench** | 科研复现 | 69 | 51 | — | TMLR 2025 | Princeton，论文可复现性评测 |
| 22 | **APEX-Agents** | 白领生产力 | 140 | 0 | 48K | TechCrunch | 极新(2026.01)但 TechCrunch 重点报道 |
| 23 | **DA-Code** | 数据科学 | 94 | 43 | — | EMNLP 2024 | 500 真实数据科学任务 |
| 24 | **SWE-PolyBench** | 多语言代码 | 82 | 40 | 1.1K | Amazon Science | Amazon 出品，多语言 SWE-bench |

### Tier 4 — 新兴/小众（引用 <40 或极新）

| 排名 | Benchmark | 赛道 | ⭐ GitHub Stars | 📚 引用数 | 🏛️ 顶会/媒体 | 影响力说明 |
|---|---|---|---|---|---|---|
| 25 | **DataSciBench** | 数据科学 | 55 | 37 | 清华 THUDM | 全数据科学生命周期 |
| 26 | **FeatureBench** | 代码 | 45 | 2 | ICLR 2026 | 极新，顶会加持，潜力大 |
| 27 | **DABstep** | 数据分析 | — | 17 | Adyen + HuggingFace | 真实金融场景，HF 联合出品 |
| 28 | **OdysseyBench** | 办公工作流 | 6 | 16 | Microsoft | 微软出品但极新 |
| 29 | **MobileWorld** | 移动端 | 170 | 10 | 阿里通义 | 阿里出品，Android 评测 |
| 30 | **DevOps-Gym** | DevOps | 22 | 2 | ICLR 2026 | 首个 DevOps 基准，顶会收录 |
| 31 | **CAIBench** | 安全元基准 | — | 10 | — | 10K+ 实例但未广泛传播 |
| 32 | **ProjDevBench** | 项目开发 | 13 | 2 | — | 从零建项目，极新 |
| 33 | **SCUBA** | CRM | 8 | 2 | Salesforce | Salesforce 出品但非常新 |
| 34 | **COMMA** | 多 Agent 协作 | — | 7 | — | 多模态多 Agent 沟通 |
| 35 | **SWE-Compass** | 多语言代码 | 17 | 1 | 快手 | 10 语言 × 8 任务，待传播 |
| 36 | **DPAI Arena** | 开发者生产力 | — | — | JetBrains → Linux Foundation | 平台型，无学术论文 |
| 37 | **CUB** | 计算机使用 | — | — | Theta Software (YC) | 7 行业端到端，无论文 |
| 38 | **UI-CUBE** | 企业 UI | — | 1 | UiPath | 企业背景但极新 |
| 39 | **CTFusion** | 安全 (live CTF) | — | — | OpenReview | 仅 OpenReview 提交 |

---

## 全量评测总成本估算

如果对**单个 Agent Package** 跑完上述 Top 15 全部基准：

| 项目 | 估算 |
|---|---|
| **总 API 成本（中位数）** | ~$15,000-30,000 |
| **总 wall-clock（并行执行各基准）** | ~80-180h（约 3-7 天连续运行） |
| **总环境搭建（工程师人工）** | ~30-50h（首次；复用后 5-10h） |
| **额外基础设施** | $500-2,000（云 VM + GPU + SaaS 沙箱） |

> **参考**：HAL (Holistic Agent Leaderboard, Princeton) 对 9 个模型 × 9 个基准做了 21,730 次 rollout，总花费 **~$40,000**。

---

## EpochX 实测 Benchmark — GitHub & 学术影响力汇总

> **数据来源**：GitHub API + Semantic Scholar API，采集时间 2026-04-05

| # | Benchmark | GitHub Repo | ⭐ Stars | 🍴 Forks | 📚 引用数 | 🏛️ 会议 | 最近更新 | EpochX 验证状态 |
|---|-----------|------------|-------:|-------:|--------:|---------|---------|--------------|
| 1 | **SWE-bench** | [SWE-bench/SWE-bench](https://github.com/SWE-bench/SWE-bench) | 4,612 | 817 | 1,794 | ICLR 2024 | 2026-04-01 | ✅ 已验证 |
| 2 | **SWE-bench Pro** | [scaleapi/SWE-bench_Pro-os](https://github.com/scaleapi/SWE-bench_Pro-os) | 334 | 50 | 55 | Scale AI | 2026-03-31 | ✅ 已验证 |
| 3 | **tau-bench (τ³)** | [sierra-research/tau2-bench](https://github.com/sierra-research/tau2-bench) | 944 | 239 | 437 | Sierra AI | 2026-04-03 | ✅ 已验证 |
| 4 | **AppWorld** | [StonyBrookNLP/appworld](https://github.com/StonyBrookNLP/appworld) | 401 | 61 | 120 | ACL 2024 最佳资源 | 2026-02-17 | ✅ 已验证 |
| 5 | **Cybench** | [andyzorigin/cybench](https://github.com/andyzorigin/cybench) | 217 | 79 | 83 | ICLR 2025 | 2025-12-13 | ✅ 已验证 |
| 6 | **WorkArena++** | [ServiceNow/WorkArena](https://github.com/ServiceNow/WorkArena) | 242 | 35 | 161 | ICML 2024 | 2026-02-23 | ⚠️ 需 ServiceNow 实例 |
| 7 | **APEX-Agents** | [Mercor-Intelligence/archipelago](https://github.com/Mercor-Intelligence/archipelago) | 140 | 23 | 0 | arXiv 2026 | 2026-04-03 | ✅ Docker 已验证 |
| 8 | **ScienceAgentBench** | [OSU-NLP-Group/ScienceAgentBench](https://github.com/OSU-NLP-Group/ScienceAgentBench) | 133 | 18 | 71 | ICLR 2025 | 2026-03-05 | ⚠️ 数据需浏览器下载 |
| 9 | **DA-Code** | [yiyihum/da-code](https://github.com/yiyihum/da-code) | 94 | 9 | 43 | EMNLP 2024 | 2026-01-12 | ✅ 已验证 |
| 10 | **CORE-Bench** | [siegelz/core-bench](https://github.com/siegelz/core-bench) | 69 | 7 | 51 | NeurIPS 2024 | 2025-11-23 | ✅ 已验证 |
| 11 | **FeatureBench** | [LiberCoders/FeatureBench](https://github.com/LiberCoders/FeatureBench) | 45 | 5 | 2 | ICLR 2026 | 2026-03-31 | ✅ CLI 已验证 |
| 12 | **DABstep** | HuggingFace only | — | — | 17 | NeurIPS 2025 投稿 | — | ✅ 已验证 |
| 13 | **DevOps-Gym** | [ucsb-mlsec/DevOps-Gym](https://github.com/ucsb-mlsec/DevOps-Gym) | 22 | 1 | 2 | ICLR 2026 | 2026-03-11 | ❌ 代码未开源 |
| 14 | **SWE-Compass** | [kwaipilot/SWE-Compass](https://github.com/kwaipilot/SWE-Compass) | 17 | 2 | 1 | arXiv 2025 | 2026-03-28 | ⚠️ datasets 版本冲突 |
| — | **CUB** | 无公开 repo | — | — | — | Theta Software | — | ❌ 无公开 repo |

**按引用量排序 Top 5**：SWE-bench (1,794) > tau-bench (437) > WorkArena (161) > AppWorld (120) > Cybench (83)

**按 Stars 排序 Top 5**：SWE-bench (4,612) > tau-bench (944) > AppWorld (401) > SWE-bench Pro (334) > WorkArena (242)

---

## 参考资源汇总

- [AI Agent Benchmark Compendium (GitHub)](https://github.com/philschmid/ai-agent-benchmark-compendium) — 综合索引
- [O-MEGA: Best AI Agent Evals & Benchmarks 2025 Guide](https://o-mega.ai/articles/the-best-ai-agent-evals-and-benchmarks-full-2025-guide) — 全景指南
- [O-MEGA: Computer Use Benchmarks Guide](https://o-mega.ai/articles/the-2025-2026-guide-to-ai-computer-use-benchmarks-and-top-ai-agents) — 计算机使用专题
- [Evidently AI: 10 AI Agent Benchmarks](https://www.evidentlyai.com/blog/ai-agent-benchmarks) — 精选解读
- [Epoch AI Benchmarks Dashboard](https://epoch.ai/benchmarks/) — 进度追踪
- [8 Benchmarks Shaping Next-Gen AI Agents](https://ainativedev.io/news/8-benchmarks-shaping-the-next-generation-of-ai-agents) — 趋势分析
- [HAL: Holistic Agent Leaderboard](https://hal.cs.princeton.edu/) — Princeton 综合 Agent 排行榜
- [SWE-bench 1 小时跑完指南 (Epoch AI)](https://epoch.ai/blog/swebench-docker/) — Docker 化加速参考
- [AI21: 从 200,000 次 SWE-bench run 学到的经验](https://www.ai21.com/blog/scaling-agentic-evaluation-swe-bench/) — 大规模评测工程实践
