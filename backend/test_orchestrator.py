import pytest
from swarm_orchestrator import SwarmOrchestrator

@pytest.mark.asyncio
async def test_process_message_multiple_agents(monkeypatch):
    orchestrator = SwarmOrchestrator()

    async def dummy_get_agent_response(agent, message, conversation_id=None):
        return {"agent_id": agent.id, "content": f"hi from {agent.name}"}

    monkeypatch.setattr(orchestrator, "_get_agent_response", dummy_get_agent_response)

    responses = await orchestrator.process_message("hello", agent_ids=["comms", "coder"])
    assert len(responses) == 2
    ids = {r["agent_id"] for r in responses}
    assert ids == {"comms", "coder"}
