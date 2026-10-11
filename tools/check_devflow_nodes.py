"""Run controlled DevFlow node tests without starting servers or using real model APIs."""

import argparse
import json
import os
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEST_FILES = [
    "test_chat_agent.py",
    "test_workflow_orchestrator.py",
    "test_context_compression.py",
    "test_context_memory_projection.py",
    "test_repos_sync.py",
    "test_rag_source_policy.py",
    "test_rag_qa.py",
    "test_rag_retrieval_pipeline.py",
    "test_rag_project_isolation.py",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--devflow-root", required=True, type=Path)
    args = parser.parse_args()
    backend = args.devflow_root.resolve() / "backend"
    python = backend / ".venv/Scripts/python.exe"
    if not python.is_file():
        python = backend / ".venv/bin/python"
    if not python.is_file():
        raise SystemExit("DevFlow backend virtual environment was not found")
    expected = [backend / "app/tests" / name for name in TEST_FILES]
    if any(not path.is_file() for path in expected):
        raise SystemExit("This DevFlow checkout does not contain all expected node tests")
    files = sorted((backend / "app/tests").glob("test_*.py"))
    runtime = ROOT / "runtime"
    runtime.mkdir(exist_ok=True)
    report_file = runtime / "devflow-node-tests.xml"
    env = dict(os.environ)
    env["PYTHONPATH"] = str(backend)
    env["PYTHONUTF8"] = "1"
    result = subprocess.run([str(python), "-m", "pytest", "-q", "-p", "no:cacheprovider", f"--junitxml={report_file}", *map(str, files), str(ROOT / "tests_devflow/test_internal_nodes.py")], cwd=backend, env=env)
    suites = ET.parse(report_file).getroot().iter("testsuite")
    report = {key: 0 for key in ("tests", "failures", "errors", "skipped")}
    for suite in suites:
        for key in report:
            report[key] += int(suite.get(key, "0"))
    report.update({"status": "passed" if result.returncode == 0 else "failed", "real_llm_calls": False, "servers_started": False})
    (runtime / "devflow-node-verification.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
