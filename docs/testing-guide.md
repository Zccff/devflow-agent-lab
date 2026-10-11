# 在 DevFlow AI 中逐步测试

本仓库提供可分析的真实 GitHub 对象与虚构代码。只有标记为故障演练的 PR/CI 应失败。模型工具选择存在变化，仓库不能独自保证触发每一条内部错误分支。

## 1. 连接与同步

在仓库接入页面选择 GitHub，Owner 填 `Zccff`，Repository 填 `devflow-agent-lab`。只读同步公开数据时可以先留空 Token。连接后再点击一次同步/刷新，获取默认上限 50 条的完整演示资料；初次接入默认数量较少。

期望看到开放与关闭的 Issue、开放与合并的 PR、成功与失败 CI。连续同步两次后，Issue/PR/CI 的 ID 与数量应保持一致，没有重复对象。

如果 GitHub 匿名接口限流，使用你自己的只读 GitHub Token 在页面配置。不要把 Token 提交到仓库。外部写操作另外需要合适的 GitHub 写权限。

## 2. 源码与代码关系图

提问：`这个项目做什么？请先读取 README 和源码，说明 checkout 到 login、validate_token、calculate_total 的调用关系。`

期望工具记录出现 workspace.list_files/read_file/search_code。代码关系图中应有登录、金额计算和 checkout 的符号及关系；索引为轻量分析，不代表完整编译器语义。

## 3. 六个 Skill 和协作工作流

| 要测试的入口 | 输入或页面操作 | 应检查的证据 |
| --- | --- | --- |
| issue-triage | `使用 issue-triage 分析最新登录 Issue，说明分类、优先级和证据。` | 登录复现、401/500、负责人缺失时不编造 |
| pr-review | `使用 pr-review 审查最新登录 PR，重点检查异常捕获和测试失败。` | diff、行级评论、失败测试 |
| ci-debug | `使用 ci-debug 分析最新失败 CI，先说明它属于哪个运行。` | job、step、日志；独立故障不能归因登录 PR |
| weekly-report | `使用 weekly-report 汇总本周 Issue、PR、CI 和阻塞项。` | 关闭 Issue、合并 PR、开放 PR、失败 CI |
| safety-draft | `使用 safety-draft 生成一条登录 PR 评论草稿，先让我确认。` | pending_confirmation 草稿；不直接外部写入 |
| project-investigation | `使用 project-investigation 结合源码、ADR 和知识库解释为什么金额不能用 float。` | 文件、当前规则、检索引用 |
| 多 Agent 工作流 | `联合分析 Issue、PR、CI 和历史文档，判断这个项目是否可以合并发布，并解释理由。` | repo_health、专用任务、Observer、Synthesis |
| 计划预览 | 先生成工作流计划，再在页面确认执行 | 任务依赖、目标范围、执行记录 |

普通聊天的专用工具可能默认选最新对象。比较不同 PR/CI 时，优先在对应列表打开指定对象并点击分析。

GitHub PR 的 review 评论与 DevFlow 的 ActionDraft 审批是不同机制。对自己创建的 PR 可以留下评论，但不能把自己的 approve 当作独立审查。

## 4. RAG、上传与评测

把 `fixtures/knowledge/lab-knowledge.md` 上传到此仓库的知识库，等状态完成。测试问题：

- `DEVFLOW_LAB_POLICY_V1 的金额计算使用什么类型、什么舍入方式？2.675 元应得到多少？`
- `这个演示项目的维护窗口、RTO、RPO 分别是什么？`
- `missing-dependency 运行缺少哪个模块？它是登录 PR 导致的吗？`
- `这家公司真实季度营收是多少？`（期望说明资料不足）

检查来源、片段、向量召回、关键词召回和重排信息。可比较 hybrid、vector、keyword，以及是否启用 rerank/阈值。

`fixtures/evals/devflow-agent-lab.json` 提供固定问题和参考答案。可以通过 DevFlow 的 `/api/evals/rag/run` 提交 `cases`；不要把它误当成已经跑出的质量评分。评测报告缺少 judge 结果时，不得宣称达到发布门槛。

## 5. 会话、记忆与压缩

在同一会话先说：`记住这次演练的发布口令是 LAB-CEDAR-731；本次决定暂缓合并，先修复登录异常捕获。`

随后分别提问：`我刚才决定了什么？`、`请核实我说的发布口令原话。`、`查看先前封存的分析记录。`

检查近期消息读取、devflow_get_thread_context、devflow_read_session_events、devflow_search_evidence 的区别；不要求每个问题都调用全部工具。

到记忆候选页面审核一条决策，再在新会话检索；拒绝另一条候选，确认它没有经该流程成为 memory_note。记忆候选审核不会删除原始聊天记录。

长对话或降低本地上下文预算可观察 warning → auto_compact → aggressive；核对摘要、最近消息、原文恢复和失败记录。不要只凭一次正常聊天声称测到了压缩和溢出。

## 6. 权限、幂等和失败分支

以下内部机制需要在本地 DevFlow 的测试或设置中控制，GitHub 仓库本身不能强制触发：

| 分支 | 可靠的测试方法 |
| --- | --- |
| max_steps_stop | 用受控模型连续返回不同工具调用，并降低测试中的步骤上限 |
| 重复工具保护 | 受控模型反复返回同一工具和相同参数 |
| 短暂错误重试 | 工具第一次抛 TimeoutError，第二次返回成功 |
| Skill 拒绝工具 | 显式 Skill 激活后，受控模型请求不在其允许列表中的工具 |
| 应用角色拒绝 | 测试 require_permission 的低权限角色；当前实际身份仍为演示用户 |
| GitHub 权限拒绝 | 使用无写权限的 Token 尝试确认演示草稿 |
| 草稿重复确认 | 用户确认一次后再次确认，检查状态拒绝和远端对象数量 |
| 子任务失败或超时 | 受控 runner 抛错/超时，检查依赖任务 skipped、Observer 与重新规划 |
| 记忆提取失败 | 受控 LLM 抛错，确认原始聊天与封存记录仍然保留 |
| 上下文溢出 | 受控模型首次抛上下文溢出错误，核对压缩重试次数 |
| Webhook | 配置仓库 webhook 指向可访问的 DevFlow URL；本地 localhost 无法直接被 GitHub 访问 |

DevFlow 源码中已有对应测试，常用文件为 test_chat_agent.py、test_workflow_orchestrator.py、test_context_compression.py、test_context_memory_projection.py、test_repos_sync.py。运行这些测试不要求修改业务源码。

本仓库另提供 4 个受控测试：步骤预算停止、显式 Skill 拒绝工具、未知工具拒绝、权限错误不重试。用 DevFlow 已安装的 Python 环境运行以下脚本，结合上述原有测试验证节点，不启动服务，也不调用真实模型：

```shell
python tools/check_devflow_nodes.py --devflow-root "你的 DevFlow-AI 路径"
```

结果保存到本地忽略目录 `runtime/`。这些受控测试与 GitHub CI 场景各有用途；正常聊天不能可靠地强制模型走每一条错误分支。

状态检查提供有限幂等；并发确认和远端成功后响应丢失仍需另外验证，不能仅凭重复点击一次就宣称完整恰好一次执行。
