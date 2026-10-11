# 本次仓库准备的验证记录

这是创建演示仓库时得到的结果，不是未来所有修改都通过的保证，也不代表已经完成真实模型效果评测。

## GitHub 演示对象

- 8 个 Issue：6 个开放、2 个关闭。
- 4 个 PR：3 个开放、1 个已合并的文档历史 PR。
- 1 条指向登录异常处理代码行的 review 评论。
- Python CI 的主分支、金额修复 PR、库存 PR 都通过。
- 登录故障 PR 的 CI 失败，已有测试报出 `500 != 401`，是故意设计的回归。
- 独立 missing-dependency、simulated-timeout 运行都失败，分别产生 ModuleNotFoundError 与 TimeoutError。

| 场景 | PR | 已验证 CI |
| --- | --- | --- |
| 历史文档 | [#9](https://github.com/Zccff/devflow-agent-lab/pull/9) | 已合并，文档测试通过 |
| 金额修复 | [#10](https://github.com/Zccff/devflow-agent-lab/pull/10) | [成功](https://github.com/Zccff/devflow-agent-lab/actions/runs/38126883830) |
| 库存模块 | [#11](https://github.com/Zccff/devflow-agent-lab/pull/11) | [成功](https://github.com/Zccff/devflow-agent-lab/actions/runs/38126891152) |
| 登录回归 | [#12](https://github.com/Zccff/devflow-agent-lab/pull/12) | [预期失败](https://github.com/Zccff/devflow-agent-lab/actions/runs/38127061423) |

独立故障：[缺依赖](https://github.com/Zccff/devflow-agent-lab/actions/runs/38127068339)、[模拟超时](https://github.com/Zccff/devflow-agent-lab/actions/runs/38127070240)。它们不能被归因到登录 PR。

## DevFlow 内部测试

运行 DevFlow 原有完整测试集 211 项，加本仓库 tests_devflow 中的 4 项受控测试：**215 passed，0 failed，0 error，0 skipped**。

新增测试覆盖 model_decision/tool_action/max_steps_stop 路径中的步骤预算停止、显式 Skill 工具拒绝、未知工具拒绝、权限失败不重试。原有测试还覆盖重复调用保护、短暂错误重试、依赖图调度、失败和超时、重新规划、记忆封存、摘要与原文恢复、Skill 注册、RAG、评测、反馈、仓库隔离等。

测试使用受控模型或模拟依赖，不调用真实模型 API，也不启动 DevFlow 服务。

## 实际同步函数验证

测试用已登录 GitHub CLI 作为网络传输，在独立测试进程里调用 DevFlow 原有 sync_repository，数据写入临时内存 SQLite。未连接或修改 DevFlow 原有 PostgreSQL/Milvus，未更改原项目源码或 .env，未提取或持久化 GitHub Token。

- 成功读取 8 个 Issue、4 个 PR、11 条当时已存在的 CI 运行。
- 保存 6 条 PR 文件记录、1 条行级 review 评论。
- 3 条失败运行都成功读取并解析日志，检出登录断言、缺依赖和模拟超时。
- 第二次同步后，Issue、PR、CI 的对象 ID 与数量不变，验证顺序执行下的去重。并发幂等未验证。
- 对 main 源码运行 DevFlow 代码关系提取，得到 43 个符号、260 条关系。这是轻量提取结果，不是完整编译器语义。
- 6 条固定评测问题通过 DevFlow 请求结构校验；尚未运行真实模型 judge。

提交验证文档后可能增加新的 CI 运行，运行总数会继续增长。

## 连接时的限制

本次实测，不携带身份凭证下载 GitHub Actions 日志返回 HTTP 403。公开基础数据可读取，但完整 CI 排查需要合适的 GitHub Token。使用 fine-grained Token 时，应选择本演示仓库并提供 Actions 读取权限；外部评论或 Issue 写入还需对应写权限与 DevFlow 草稿确认。

上传知识文件、实际 Qwen 对话、长期记忆审核、工作流计划确认、Webhook 联通与真实模型评测，按测试指南在 DevFlow 中继续执行。提供仓库和通过受控测试不等于已经实际跑过所有交互与故障分支。
