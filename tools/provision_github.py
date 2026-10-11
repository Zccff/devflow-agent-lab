"""Create/reuse only this synthetic lab's GitHub fixtures using an authenticated gh CLI.

No token is read, written or committed. Local author identity is repository-scoped.
Re-running reuses marker-tagged issues/PRs and does not merge the regression PR.
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = "Zccff/devflow-agent-lab"
DESCRIPTION = "DevFlow AI synthetic lab: issues, PR reviews, passing/failing CI, RAG and memory scenarios"
MANIFEST = ROOT / "fixtures/scenarios.json"


class Provisioner:
    def __init__(self, gh: str):
        self.gh = shutil.which(gh) or str(Path(gh).resolve())
        if not Path(self.gh).is_file():
            raise RuntimeError("GitHub CLI executable was not found")
        self.manifest = {"repository": REPO, "url": f"https://github.com/{REPO}", "synthetic_only": True, "issues": [], "pull_requests": []}

    def command(self, args, *, check=True):
        result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
        if check and result.returncode:
            raise RuntimeError(f"{args[0]} command failed: {result.stderr.strip()} {result.stdout.strip()}")
        return result

    def git(self, *args):
        return self.command(["git", *args]).stdout.strip()

    def api(self, method, endpoint, payload=None):
        args = [self.gh, "api", "--method", method, endpoint]
        with tempfile.TemporaryDirectory(prefix="devflow-lab-request-") as temporary:
            if payload is not None:
                request = Path(temporary) / "request.json"
                request.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
                args += ["--input", str(request)]
            result = self.command(args)
        return json.loads(result.stdout) if result.stdout.strip() else None

    def write(self, relative, content):
        target = ROOT / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    def checkpoint(self):
        self.write("runtime/provision-state.json", json.dumps(self.manifest, ensure_ascii=False, indent=2) + "\n")

    def commit(self, message):
        self.git("add", "--", ".")
        if self.git("diff", "--cached", "--name-only"):
            self.git("commit", "-m", message)

    def initialize(self):
        user = self.api("GET", "user")
        if user["login"] != "Zccff":
            raise RuntimeError("The authenticated account must match the user-approved repository owner Zccff")
        if not (ROOT / ".git").exists():
            self.git("init", "-b", "main")
        self.git("config", "user.name", "Zccff")
        self.git("config", "user.email", f"{user['id']}+Zccff@users.noreply.github.com")
        self.git("config", "core.autocrlf", "false")
        helper = f'!"{Path(self.gh).resolve().as_posix()}" auth git-credential'
        self.git("config", "credential.https://github.com.helper", "")
        self.git("config", "--add", "credential.https://github.com.helper", helper)
        remotes = self.git("remote")
        if "origin" not in remotes.splitlines():
            self.checkpoint()
            self.write("fixtures/scenarios.json", json.dumps(self.manifest, ensure_ascii=False, indent=2) + "\n")
            self.commit("Create synthetic order service and DevFlow test guide")
            probe = self.command([self.gh, "api", f"repos/{REPO}"], check=False)
            if probe.returncode == 0:
                raise RuntimeError("Remote repository already exists without a local origin; refusing to adopt it automatically")
            if "404" not in probe.stderr and "Not Found" not in probe.stdout:
                raise RuntimeError("Cannot verify whether the destination repository exists")
            self.command([self.gh, "repo", "create", REPO, "--public", "--description", DESCRIPTION, "--source", str(ROOT), "--remote", "origin", "--push"])
        else:
            remote = self.git("remote", "get-url", "origin")
            if remote.removesuffix(".git") not in {f"https://github.com/{REPO}", f"git@github.com:{REPO}"}:
                raise RuntimeError("Origin does not point to the approved synthetic repository")
            metadata = self.api("GET", f"repos/{REPO}")
            if metadata["description"] != DESCRIPTION or metadata["private"]:
                raise RuntimeError("Repository ownership/description/visibility no longer matches this lab")
        self.git("checkout", "main")
        self.git("fetch", "origin", "main")
        self.git("merge", "--ff-only", "origin/main")
        print(f"Repository ready: https://github.com/{REPO}", flush=True)

    def labels(self):
        existing = {item["name"] for item in self.api("GET", f"repos/{REPO}/labels?per_page=100")}
        for name, color in [("lab-fixture", "0e8a16"), ("auth", "d93f0b"), ("billing", "5319e7"), ("inventory", "1d76db"), ("ci", "fbca04"), ("priority:P1", "b60205")]:
            if name not in existing:
                self.api("POST", f"repos/{REPO}/labels", {"name": name, "color": color, "description": "Synthetic DevFlow lab fixture"})

    def issues(self):
        records = self.api("GET", f"repos/{REPO}/issues?state=all&per_page=100")
        specs = [
            ("rounding", "[Bug] 金额 2.675 被舍入为 2.67，违反 ROUND_HALF_UP", ["bug", "billing"], "复现：calculate_total('2.675', 1)。实际 2.67，期望 2.68；2.685 应为 2.69。请按 ADR-0001 使用 Decimal。main 的普通金额测试尚未覆盖这一边界。验收：边界测试通过。"),
            ("inventory", "[Feature] 库存扣减模块与单次最多 5 件的校验", ["enhancement", "inventory"], "新增 reserve_stock；拒绝 0、负数、超过 5 件、库存不足。正常扣减返回剩余库存。先提供独立模块与测试，接入 checkout 是后续任务。"),
            ("runbook", "[Docs] 补充发布与回滚检查清单", ["documentation"], "发布前检查 CI、review 和关联 Issue；维护窗口周三 20:00-20:30 Asia/Shanghai，RTO 10 分钟，RPO 5 分钟。该 Issue 在文档 PR 合并后关闭，用于测试历史与周报。"),
            ("dependency", "[CI] 独立故障演练：缺少 lab_optional_gateway", ["bug", "ci"], "Deliberate failure lab / missing-dependency 应报 ModuleNotFoundError。这是人为设计的演练，不涉及真实依赖安装，不能归因到登录 PR。验收：CI Agent 指出缺依赖类型和演练性质。"),
            ("timeout", "[CI] 独立故障演练：模拟网关请求超时", ["bug", "ci"], "Deliberate failure lab / simulated-timeout 应报 TimeoutError。没有发出真实网络请求。用于分析失败 job、step、日志和下一步；它不会强制触发 DevFlow 内部工具重试分支。"),
            ("status-question", "[Question] 凭证失效应返回 401 还是 403？", ["question", "auth"], "请结合 ADR-0001 解释：过期/无效凭证返回 401；已认证但缺少资源访问权限时用 403。需要附文档依据。"),
            ("login-history", "[历史 Bug] 登录凭证过期导致 500，已记录处理规则", ["bug", "auth"], "历史演练问题：过期凭证落入通用异常返回 500。决定显式捕获 ExpiredTokenError 并返回 401。此条关闭，供相似 Issue 检索；最新开放登录 Bug 展示同类回归。"),
            ("login-current", "[Bug][P1] 登录凭证过期从 401 回归为 500", ["bug", "auth", "priority:P1"], "步骤：login('demo-user:900', now=1000)。期望 status=401。登录故障 PR 故意遗漏 ExpiredTokenError 捕获，实际 status=500。受影响：过期凭证及 checkout 登录门禁。检查 test_expired_credential_returns_401、test_expiry_boundary_returns_401 和 test_checkout_rejects_expired_credential。禁止仅凭 main CI 成功就推荐合并该 PR。"),
        ]
        by_key = {}
        for key, title, labels, body in specs:
            marker = f"<!-- devflow-agent-lab:issue:{key} -->"
            issue = next((item for item in records if "pull_request" not in item and marker in (item.get("body") or "")), None)
            if issue is None:
                issue = self.api("POST", f"repos/{REPO}/issues", {"title": title, "body": f"{marker}\n\n这是虚构测试场景。\n\n{body}", "labels": ["lab-fixture", *labels], "assignees": ["Zccff"] if key in {"rounding", "login-current"} else []})
                records.append(issue)
            if key == "login-history" and issue["state"] == "open":
                issue = self.api("PATCH", f"repos/{REPO}/issues/{issue['number']}", {"state": "closed"})
            by_key[key] = issue
            self.manifest["issues"].append({"key": key, "number": issue["number"], "url": issue["html_url"]})
            self.checkpoint()
            print(f"Issue {key}: {issue['html_url']}", flush=True)
        return by_key

    def make_pr(self, key, branch, title, body, files, expected_success, issues):
        prs = self.api("GET", f"repos/{REPO}/pulls?state=all&per_page=100")
        marker = f"<!-- devflow-agent-lab:pr:{key} -->"
        pr = next((item for item in prs if marker in (item.get("body") or "")), None)
        if pr is None:
            self.git("checkout", "main")
            self.git("checkout", "-b", branch)
            for name, content in files.items():
                self.write(name, content)
            result = self.command([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], check=False)
            log = ROOT / "runtime" / f"{key}-local-tests.log"
            log.parent.mkdir(exist_ok=True)
            log.write_text(result.stdout + result.stderr, encoding="utf-8")
            if (result.returncode == 0) != expected_success:
                raise RuntimeError(f"Unexpected unit-test outcome for {key}: see {log}")
            self.commit(title)
            self.git("push", "-u", "origin", branch)
            pr = self.api("POST", f"repos/{REPO}/pulls", {"title": title, "head": branch, "base": "main", "body": f"{marker}\n\n{body}"})
        self.manifest["pull_requests"].append({"key": key, "number": pr["number"], "url": pr["html_url"], "branch": branch, "expected_ci": "success" if expected_success else "failure"})
        self.checkpoint()
        print(f"PR {key}: {pr['html_url']}", flush=True)
        if key == "runbook":
            detail = self.api("GET", f"repos/{REPO}/pulls/{pr['number']}")
            if not detail.get("merged"):
                if detail["state"] != "open":
                    raise RuntimeError("Historical runbook PR was closed without merging")
                self.api("PUT", f"repos/{REPO}/pulls/{pr['number']}/merge", {"merge_method": "squash", "commit_title": title})
            issue = issues["runbook"]
            if self.api("GET", f"repos/{REPO}/issues/{issue['number']}")["state"] != "closed":
                self.api("PATCH", f"repos/{REPO}/issues/{issue['number']}", {"state": "closed"})
            self.git("checkout", "main")
            self.git("fetch", "origin", "main")
            self.git("merge", "--ff-only", "origin/main")
        return pr

    def pull_requests(self, issues):
        self.make_pr("runbook", "docs/release-runbook", "docs: 发布回滚清单（历史合并场景）", f"补充已知发布契约。Closes #{issues['runbook']['number']}。仅改文档，测试应通过。", {"docs/release-runbook.md": "# 发布与回滚清单\n\n- 确认当前 PR 的 CI 成功，而不只是 main 的 CI 成功。\n- 核查 review 评论与关联 Issue。\n- 维护窗口：周三 20:00-20:30 Asia/Shanghai。\n- 回滚 RTO：10 分钟；备份 RPO：5 分钟。\n- 写入 GitHub 或发布前必须人工确认。\n"}, True, issues)
        self.make_pr("rounding-fix", "fix/decimal-rounding", "fix: 使用 Decimal 修复金额舍入并补充边界测试", f"Refs #{issues['rounding']['number']}。用字符串构造 Decimal，按 ROUND_HALF_UP 保留两位小数。新增 2.675、2.685 和批量金额测试；CI 应通过。尚未合并，适合对照故障 PR。", {
            "demo_service/billing.py": 'from decimal import Decimal, ROUND_HALF_UP\n\n\ndef calculate_total(unit_price: str, quantity: int) -> str:\n    if quantity <= 0:\n        raise ValueError("quantity must be positive")\n    total = Decimal(unit_price) * quantity\n    return format(total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), ".2f")\n',
            "tests/test_rounding.py": 'import unittest\n\nfrom demo_service.billing import calculate_total\n\n\nclass RoundingTests(unittest.TestCase):\n    def test_2675_rounds_half_up(self):\n        self.assertEqual(calculate_total("2.675", 1), "2.68")\n\n    def test_2685_rounds_half_up(self):\n        self.assertEqual(calculate_total("2.685", 1), "2.69")\n\n    def test_batch_price_rounds_after_multiplication(self):\n        self.assertEqual(calculate_total("2.675", 3), "8.03")\n'
        }, True, issues)
        self.make_pr("inventory", "feature/inventory-guard", "feat: 新增库存扣减模块及边界测试", f"Refs #{issues['inventory']['number']}。新增独立 reserve_stock 模块，覆盖数量和库存边界，CI 应通过。暂未接入 checkout，也未实现并发库存控制，审查时应明确这两个范围限制。", {
            "demo_service/inventory.py": 'MAX_ORDER_QUANTITY = 5\n\n\ndef reserve_stock(stock: int, quantity: int) -> int:\n    if quantity <= 0 or quantity > MAX_ORDER_QUANTITY:\n        raise ValueError("quantity must be between 1 and 5")\n    if stock < quantity:\n        raise ValueError("insufficient stock")\n    return stock - quantity\n',
            "tests/test_inventory.py": 'import unittest\n\nfrom demo_service.inventory import reserve_stock\n\n\nclass InventoryTests(unittest.TestCase):\n    def test_normal_reservation(self):\n        self.assertEqual(reserve_stock(10, 3), 7)\n\n    def test_exact_stock(self):\n        self.assertEqual(reserve_stock(5, 5), 0)\n\n    def test_non_positive_quantity(self):\n        for quantity in (0, -1):\n            with self.subTest(quantity=quantity), self.assertRaises(ValueError):\n                reserve_stock(10, quantity)\n\n    def test_quantity_limit(self):\n        with self.assertRaises(ValueError):\n            reserve_stock(10, 6)\n\n    def test_insufficient_stock(self):\n        with self.assertRaises(ValueError):\n            reserve_stock(2, 3)\n'
        }, True, issues)
        self.git("checkout", "main")
        auth = (ROOT / "demo_service/auth.py").read_text(encoding="utf-8")
        faulty = auth.replace("except (InvalidTokenError, ExpiredTokenError):", "except InvalidTokenError:")
        if faulty == auth:
            raise RuntimeError("Cannot locate the intended authentication regression")
        bad = self.make_pr("login-regression", "lab/login-expiry-regression", "lab: 登录过期处理回归，保留失败 CI 供审查", f"Refs #{issues['login-current']['number']}。这是故意引入缺陷的演练 PR，不应合并。移除 ExpiredTokenError 捕获后，过期凭证落入 500 分支；预计 3 个已有测试失败。请核对 diff、行级 review 评论和此分支的 CI。", {"demo_service/auth.py": faulty}, False, issues)
        comments = self.api("GET", f"repos/{REPO}/pulls/{bad['number']}/comments?per_page=100")
        marker = "<!-- devflow-agent-lab:review:expired-token -->"
        if not any(marker in (item.get("body") or "") for item in comments):
            detail = self.api("GET", f"repos/{REPO}/pulls/{bad['number']}")
            line = next(index for index, text in enumerate(faulty.splitlines(), 1) if "except InvalidTokenError:" in text)
            comment = self.api("POST", f"repos/{REPO}/pulls/{bad['number']}/comments", {"body": f"{marker}\n\n[P1] 这里遗漏 ExpiredTokenError，过期凭证会落入通用异常并返回 500。请恢复显式捕获并核对三个登录门禁测试。该演练 PR 需保持未合并。", "commit_id": detail["head"]["sha"], "path": "demo_service/auth.py", "line": line, "side": "RIGHT"})
            self.manifest["inline_review_url"] = comment["html_url"]
        elif comments:
            self.manifest["inline_review_url"] = next(item["html_url"] for item in comments if marker in (item.get("body") or ""))

    def finish(self):
        self.git("checkout", "main")
        self.checkpoint()
        self.write("fixtures/scenarios.json", json.dumps(self.manifest, ensure_ascii=False, indent=2) + "\n")
        self.commit("Document generated GitHub scenario links")
        self.git("push", "origin", "main")
        runs = self.api("GET", f"repos/{REPO}/actions/runs?per_page=100")["workflow_runs"]
        for scenario in ("missing-dependency", "simulated-timeout"):
            if not any(run.get("display_title") == f"Failure lab / {scenario}" for run in runs):
                self.api("POST", f"repos/{REPO}/actions/workflows/failure-lab.yml/dispatches", {"ref": "main", "inputs": {"scenario": scenario}})
        print("Provisioned. GitHub Actions may still be running; verify their final conclusions.", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gh", default="gh", help="Path to authenticated GitHub CLI")
    args = parser.parse_args()
    provisioner = Provisioner(args.gh)
    provisioner.initialize()
    provisioner.labels()
    issues = provisioner.issues()
    provisioner.pull_requests(issues)
    provisioner.finish()


if __name__ == "__main__":
    main()
