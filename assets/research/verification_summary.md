# EpochX Benchmark 验证状态总结

> 验证时间：2026-04-05

---

## ✅ 端到端验证通过（6个）

| Benchmark | 验证任务 | 结果 | 耗时 | 成本 | 方式 |
|---|---|---|---|---|---|
| DABstep | Task #5 | 答案 "NL" ✅ | 19.7s | <$0.05 | claude -p + sonnet, git lfs pull 后读 CSV |
| tau-bench | retail task #0 | Reward=1.0 ✅ | ~30s | $0.0072 | OpenRouter gemini-flash, uv run tau2 |
| Cybench | Dynastic (Very Easy) | 正确 flag ✅ | 38.4s | <$0.05 | claude -p 直接逆向，无需 Docker |
| DA-Code | data-sa-001 (Hard) | p_val=2.10e-127, reject ✅ | 47s | <$0.10 | claude -p 读 CSV + pandas t-test |
| SWE-bench Pro | pallets__flask-5014 | 正确 patch ✅ | 24.7s | <$0.05 | git clone → claude -p 修代码 → git diff |
| CORE-Bench | capsule-3137115 (R, Social Sci) | Docker --privileged 执行成功 ✅ | ~5min | <$0.10 | conda → gpg 解密 → Docker build → 执行 |

---

## ✅ CLI/测试框架验证通过（3个）

| Benchmark | 验证内容 | 状态 | 备注 |
|---|---|---|---|
| FeatureBench | pip install + fb CLI | CLI 可用 ✅ | 原生 --agent claude_code 支持，最佳集成 |
| AppWorld | appworld verify tests | 110/112 tests passed ✅ | conda 3.11 → install --repo → download data |
| APEX-Agents | Docker image + container | 镜像构建 2.86GB，world snapshot loaded ✅ | MCP 503 timing issue 未完全解决 |

---

## ⚠️ 部分验证 / 有阻塞（3个）

| Benchmark | 已完成 | 阻塞原因 | 可解决性 |
|---|---|---|---|
| ScienceAgentBench | HuggingFace 数据集加载 OK (102 tasks) | 评测数据需 SharePoint 浏览器登录下载 | 需用户手动浏览器下载，密码 scienceagentbench |
| SWE-Compass | 仓库已克隆 | datasets 库版本冲突，load_dataset 失败 | 需单独 conda env + 兼容版本 datasets |
| WorkArena++ | 代码已安装 | 需 ServiceNow Developer Instance（免费但需注册审批） | 需用户注册 ServiceNow 开发者账号 |

---

## ❌ 无法使用（2个）

| Benchmark | 原因 | 备注 |
|---|---|---|
| CUB | Theta Software 私有，无公开仓库 | YC 公司产品，仅有博客介绍 |
| DevOps-Gym | 代码未开源（ICLR 2026 论文已发表但 repo 未公开） | GitHub 有 repo 但内容极少(22 stars) |

---

## 后续行动

- **批量评测优先选**：6 个端到端通过的 benchmark
- **3 个阻塞项**需先解决前置条件（浏览器下载 / conda env / ServiceNow 注册）
- **2 个不可用**暂时跳过
