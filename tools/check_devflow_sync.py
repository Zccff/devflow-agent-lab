"""Exercise the real DevFlow synchronizer against GitHub fixtures in a temporary DB.

Authenticated transport uses gh's credential store without extracting a token.
GitHubClient's HTTP transport is replaced only inside this test process. No server,
production database, .env, application source, or GitHub object is modified.
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlencode
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--devflow-root", required=True, type=Path)
    parser.add_argument("--gh", default="gh")
    args = parser.parse_args()
    backend = args.devflow_root.resolve() / "backend"
    sys.path.insert(0, str(backend))
    os.chdir(backend)

    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from app.db.models import CodeRelation, CodeSymbol, Issue, PRFile, PRReviewComment, PullRequest, Repository, WorkflowRun
    from app.db.session import Base
    from app.schemas.evals import RagEvalCaseRequest
    from app.schemas.repos import RepoSyncRequest
    from app.services.code_analysis import _sync_code_graph
    from app.services.github.client import GitHubClient
    from app.services.repos_sync import sync_repository

    endpoint_prefix = "/repos/Zccff/devflow-agent-lab"
    cache = {}

    def read_github(path, params=None, binary=False):
        if not path.startswith(endpoint_prefix + "/"):
            raise RuntimeError("This test transport is limited to the synthetic repository")
        endpoint = path + ("?" + urlencode(params) if params else "")
        key = (endpoint, binary)
        if key not in cache:
            result = subprocess.run([args.gh, "api", "--method", "GET", endpoint], capture_output=True)
            if result.returncode:
                raise RuntimeError(result.stderr.decode("utf-8", errors="replace"))
            cache[key] = result.stdout if binary else json.loads(result.stdout.decode("utf-8"))
        return cache[key]

    async def get_json(client, path, params=None):
        return await asyncio.to_thread(read_github, path, params)

    async def get_bytes(client, path):
        return await asyncio.to_thread(read_github, path, None, True)

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        repo = Repository(owner="Zccff", name="devflow-agent-lab", full_name="Zccff/devflow-agent-lab", provider="github", api_base_url="https://api.github.com", default_branch="main", local_path=str(ROOT), checkout_mode="local")
        db.add(repo)
        db.commit()

        def snapshot():
            return {model.__name__: sorted(str(row.id) for row in db.query(model).all()) for model in (Issue, PullRequest, WorkflowRun)}

        with patch.object(GitHubClient, "get", get_json), patch.object(GitHubClient, "get_bytes", get_bytes):
            first = asyncio.run(sync_repository(db, repo, RepoSyncRequest(limit=50)))
            before = snapshot()
            second = asyncio.run(sync_repository(db, repo, RepoSyncRequest(limit=50)))
            after = snapshot()
        assert before == after, "Sequential resync changed object IDs or created duplicates"
        assert len(after["Issue"]) == 8 and len(after["PullRequest"]) == 4
        comments = db.query(PRReviewComment).all()
        assert comments and any("ExpiredTokenError" in (item.body or "") for item in comments)
        failed = db.query(WorkflowRun).filter(WorkflowRun.conclusion == "failure").all()
        assert len(failed) >= 3 and all(item.logs_text for item in failed)
        all_logs = "\n".join(item.logs_text or "" for item in failed)
        assert "500 != 401" in all_logs
        assert "ModuleNotFoundError" in all_logs and "lab_optional_gateway" in all_logs
        assert "TimeoutError" in all_logs
        sha = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
        symbols = _sync_code_graph(db, repo, ROOT, branch="main", commit_sha=sha)
        db.commit()
        assert symbols > 0 and db.query(CodeRelation).count() > 0
        cases = json.loads((ROOT / "fixtures/evals/devflow-agent-lab.json").read_text(encoding="utf-8"))["cases"]
        for item in cases:
            RagEvalCaseRequest.model_validate(item)
        report = {"status": "passed", "repository": repo.full_name, "transport": "authenticated GitHub CLI; real sync logic", "database": "temporary in-memory SQLite", "synced": first.model_dump(mode="json"), "resync": second.model_dump(mode="json"), "sequential_idempotence": True, "pr_files": db.query(PRFile).count(), "review_comments": len(comments), "failed_runs_with_logs": len(failed), "code_symbols": db.query(CodeSymbol).count(), "code_relations": db.query(CodeRelation).count(), "eval_cases_schema_valid": len(cases), "real_llm_calls": False, "servers_started": False}
        output = ROOT / "runtime/devflow-sync-verification.json"
        output.parent.mkdir(exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
