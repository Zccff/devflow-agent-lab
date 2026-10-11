# 虚构订单服务的结构

本仓库用于测试 DevFlow AI，不运行真实支付、账号或外部业务。

调用链：`checkout` → `login` → `validate_token`；身份通过后，`checkout` → `calculate_total`。

- `demo_service/auth.py`：识别有效、格式错误和过期的演示凭证。
- `demo_service/billing.py`：计算订单金额。main 保留一个已知的浮点舍入问题，修复 PR 提供 Decimal 方案。
- `demo_service/service.py`：协调身份校验与金额计算。
- `tests/`：测试主流程和凭证边界；舍入修复 PR 增加金额边界测试。

登录异常场景：过期凭证应返回 401，不能落入返回 500 的兜底分支。故障 PR 故意移除对 ExpiredTokenError 的显式捕获，生成真实失败的测试日志。

CI 关联必须使用运行的分支、commit SHA 和 PR 信息核对。手动触发的 missing-dependency、simulated-timeout 是独立的演示故障，不能当作登录 PR 导致的失败。
