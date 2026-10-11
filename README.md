# DevFlow Agent Lab

一个公开、只含虚构数据的 DevFlow AI 测试仓库。用小型 Python 订单服务制造关联的 Issue、PR、审查意见和 CI，帮助观察 Agent 从证据到结论的全过程。

## 快速接入

- 仓库：`https://github.com/Zccff/devflow-agent-lab`
- DevFlow Owner：`Zccff`
- DevFlow Repository：`devflow-agent-lab`
- 连接后再同步一次，以获取所有演示对象。
- 上传 `fixtures/knowledge/lab-knowledge.md`，测试知识问答和引用。

详细步骤见 [测试指南](docs/testing-guide.md)。生成后的对象链接保存在 [场景清单](fixtures/scenarios.json)。

本次准备时，DevFlow 原有 211 项测试加本仓库新增 4 项受控节点测试共 **215 项通过**；真实 GitHub 对象也经过 DevFlow 同步函数的临时数据库验证。详情见 [验证记录](docs/verification.md)。真实模型问答和 RAG 质量评测需要连接仓库后另行执行。

## 仓库里有什么

- `main`：基础登录与订单测试应通过；保留一个有明确 Issue 的金额舍入边界缺陷。
- 登录故障 PR：故意漏掉过期异常处理，CI 应失败，适合 PR 审查和 CI 排查。
- 金额修复 PR：Decimal + ROUND_HALF_UP，新增边界测试，CI 应通过。
- 库存功能 PR：数量校验、扣减与边界测试，CI 应通过。
- 文档历史 PR：合并到 main，提供历史合并与关闭 Issue 的周报资料。
- 手动故障 CI：缺依赖、模拟超时，均故意失败，且不涉及真实外部请求。
- 项目架构、ADR、上传知识文件、固定评测问题、内部节点测试方法。

## 本地运行

Python 3.12 或更新版本，无第三方运行依赖：

```shell
python -m unittest discover -s tests -v
```

各 PR 的成败是有意设计的，不能把故障 PR 合并到 main 来消除演练场景。

## 覆盖范围

仓库直接提供 Issue、PR、CI、diff、行级 review 评论、源码与文档证据。记忆审核、工作流计划确认、工具权限、上下文压缩和重试需在 DevFlow 内操作或受控测试触发，详见指南。仓库中提供资料不等于所有节点已实际执行通过。

这是分析用的演示代码，不提供真实账号、支付服务、密钥、生产部署或第三方人员资料。
