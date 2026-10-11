"""Controlled tests against an installed DevFlow checkout. No real LLM or GitHub calls."""

import pytest
from langchain_core.messages import AIMessage

from app.services.agents.chat_agent import ChatAgent
from app.services.skills import get_skill_registry


class ScriptedModel:
    def __init__(self, tool="lab__probe", continuous=False):
        self.tool = tool
        self.continuous = continuous
        self.calls = 0

    def bind_tools(self, tools):
        return self

    async def ainvoke(self, messages):
        self.calls += 1
        if self.continuous or self.calls == 1:
            return AIMessage(content="", tool_calls=[{"name": self.tool, "args": {"query": f"step-{self.calls}"}, "id": f"lab-{self.calls}"}])
        return AIMessage(content="The tool result has been observed.")


async def final_result(agent, context):
    events = [event async for event in agent.run_stream({"message": "Execute the requested analysis probe."}, context)]
    return next(event["data"] for event in reversed(events) if event["event"] == "final")


@pytest.mark.asyncio
async def test_lab_hits_max_steps_stop_with_distinct_calls():
    invoked = []

    async def probe(input_data, context):
        invoked.append(input_data["query"])
        return {"route": "lab_probe", "answer": "Synthetic evidence", "citations": []}

    agent = ChatAgent(model=ScriptedModel(continuous=True))
    agent.max_steps = 2
    result = await final_result(agent, {"tools": {"lab.probe": probe}})
    assert len(invoked) == 2 and len(set(invoked)) == 2
    assert result["completion"]["reason"] == "max_steps_exhausted"
    assert result["route"] == "tool_loop_budget_exhausted"


@pytest.mark.asyncio
async def test_lab_explicit_skill_denies_unlisted_registered_tool():
    invoked = []

    async def probe(input_data, context):
        invoked.append(input_data)
        return {"answer": "This function must not execute"}

    result = await final_result(ChatAgent(model=ScriptedModel()), {"tools": {"lab.probe": probe}, "_skill_registry": get_skill_registry(), "requested_skill": "pr-review"})
    assert invoked == []
    assert result["tool_calls"][0]["error_kind"] == "permission_denied"
    assert result["tool_calls"][0]["retryable"] is False


@pytest.mark.asyncio
async def test_lab_unknown_tool_never_executes_registered_probe():
    invoked = []

    async def probe(input_data, context):
        invoked.append(input_data)
        return {"answer": "This function must not execute"}

    result = await final_result(ChatAgent(model=ScriptedModel(tool="lab__nonexistent")), {"tools": {"lab.probe": probe}})
    assert invoked == []
    assert result["tool_calls"][0]["error_kind"] == "unknown_tool"


@pytest.mark.asyncio
async def test_lab_permission_failure_is_not_retried():
    invoked = []

    async def probe(input_data, context):
        invoked.append(input_data)
        raise PermissionError("403 forbidden: synthetic test permission")

    result = await final_result(ChatAgent(model=ScriptedModel()), {"tools": {"lab.probe": probe}})
    assert len(invoked) == 1
    assert result["tool_calls"][0]["error_kind"] == "permission_denied"
    assert result["tool_calls"][0]["attempts"] == 1
