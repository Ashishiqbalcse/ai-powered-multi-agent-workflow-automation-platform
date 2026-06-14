from app.agents.orchestrator import OrchestratorAgent


def test_heuristic_plan_uses_expected_agents() -> None:
    plan = OrchestratorAgent()._heuristic_plan(
        "Research top AI startups, compare the data in a table, and save a PDF"
    )

    agents = {step["agent_name"] for step in plan}
    assert "web_search" in agents
    assert "data_analysis" in agents
    assert "code_execution" in agents
    assert any(step["requires_approval"] for step in plan)

