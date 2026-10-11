"""Verify the provisioned GitHub objects; do not modify or rerun any workflow."""

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gh", default="gh")
    args = parser.parse_args()
    manifest = json.loads((ROOT / "fixtures/scenarios.json").read_text(encoding="utf-8"))
    repo = manifest["repository"]

    def api(endpoint):
        result = subprocess.run([args.gh, "api", endpoint], check=True, capture_output=True, text=True, encoding="utf-8")
        return json.loads(result.stdout)

    metadata = api(f"repos/{repo}")
    assert metadata["private"] is False
    issues = api(f"repos/{repo}/issues?state=all&per_page=100")
    issues = [item for item in issues if "pull_request" not in item]
    prs = api(f"repos/{repo}/pulls?state=all&per_page=100")
    runs = api(f"repos/{repo}/actions/runs?per_page=100")["workflow_runs"]
    checks = []
    assert len(issues) >= 8 and len(prs) >= 4
    for item in manifest["pull_requests"]:
        pr = api(f"repos/{repo}/pulls/{item['number']}")
        if item["key"] == "runbook":
            assert pr["merged"] is True
            checks.append({"key": item["key"], "state": "merged", "url": item["url"]})
            continue
        assert pr["state"] == "open" and not pr["merged"]
        candidates = [run for run in runs if run["name"] == "Python CI" and run["head_sha"] == pr["head"]["sha"] and run["event"] == "pull_request"]
        assert candidates, f"No matching CI for {item['key']}"
        run = max(candidates, key=lambda row: row["id"])
        assert run["status"] == "completed", f"CI still running for {item['key']}"
        assert run["conclusion"] == item["expected_ci"], f"Unexpected CI conclusion for {item['key']}: {run['conclusion']}"
        checks.append({"key": item["key"], "state": pr["state"], "ci": run["conclusion"], "run_id": run["id"], "run_url": run["html_url"], "url": item["url"]})
    main_sha = api(f"repos/{repo}/commits/main")["sha"]
    baseline = [run for run in runs if run["name"] == "Python CI" and run["head_sha"] == main_sha]
    assert baseline and max(baseline, key=lambda row: row["id"])["conclusion"] == "success", "Current main CI has not passed"
    comments = api(f"repos/{repo}/pulls/{next(item['number'] for item in manifest['pull_requests'] if item['key'] == 'login-regression')}/comments?per_page=100")
    assert any("ExpiredTokenError" in item["body"] for item in comments)
    for scenario in ("missing-dependency", "simulated-timeout"):
        matched = [run for run in runs if run["display_title"] == f"Failure lab / {scenario}"]
        assert matched and max(matched, key=lambda row: row["id"])["conclusion"] == "failure", f"Expected deliberate failure for {scenario}"
    report = {"status": "passed", "repository": repo, "issues": len(issues), "open_issues": sum(item["state"] == "open" for item in issues), "closed_issues": sum(item["state"] == "closed" for item in issues), "pull_requests": len(prs), "inline_comments": len(comments), "workflow_runs": len(runs), "main_ci": "success", "checks": checks}
    output = ROOT / "runtime/github-verification.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
