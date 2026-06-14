from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.agents.state import AgentState
from app.services.llm import LLMClient


AGENT_NAMES = {"web_search", "code_execution", "data_analysis"}


class OrchestratorAgent:
    name = "orchestrator"

    async def plan(self, *, db: Session, run_id: str, goal: str) -> list[dict[str, Any]]:
        fallback = {"subtasks": self._heuristic_plan(goal)}
        llm = LLMClient(db)
        response = await llm.complete_json(
            run_id=run_id,
            agent_name=self.name,
            system_prompt=(
                "You are an autonomous workflow orchestrator. Break the user's goal into "
                "ordered subtasks. Return JSON only with key `subtasks`. Each subtask must "
                "include: title, agent_name, objective, input, requires_approval, risk_level."
            ),
            user_prompt=f"Goal: {goal}",
            fallback=fallback,
        )
        subtasks = response.get("subtasks") or fallback["subtasks"]
        return [self._normalize_subtask(item, i) for i, item in enumerate(subtasks)]

    def build_langgraph(self):
        try:
            from langgraph.graph import END, StateGraph
        except ImportError:
            return None

        workflow = StateGraph(AgentState)
        workflow.add_node("plan", self._graph_plan_node)
        workflow.add_node("approval_gate", self._graph_approval_node)
        workflow.add_node("synthesize", self._graph_synthesize_node)
        workflow.set_entry_point("plan")
        workflow.add_edge("plan", "approval_gate")
        workflow.add_conditional_edges(
            "approval_gate",
            lambda state: "stop" if state.get("requires_approval") else "synthesize",
            {"stop": END, "synthesize": "synthesize"},
        )
        workflow.add_edge("synthesize", END)
        return workflow.compile()

    async def _graph_plan_node(self, state: AgentState) -> AgentState:
        state["subtasks"] = self._heuristic_plan(state["goal"])
        return state

    async def _graph_approval_node(self, state: AgentState) -> AgentState:
        risky = [task for task in state.get("subtasks", []) if task.get("requires_approval")]
        state["requires_approval"] = bool(risky)
        state["approval_plan"] = {"subtasks": risky}
        return state

    async def _graph_synthesize_node(self, state: AgentState) -> AgentState:
        state["summary"] = "Workflow ready for execution."
        return state

    def _normalize_subtask(self, subtask: dict[str, Any], index: int) -> dict[str, Any]:
        agent_name = subtask.get("agent_name", "web_search")
        if agent_name not in AGENT_NAMES:
            agent_name = "web_search"
        return {
            "id": subtask.get("id", f"step-{index + 1}"),
            "title": subtask.get("title") or f"Step {index + 1}",
            "agent_name": agent_name,
            "objective": subtask.get("objective") or subtask.get("title") or "",
            "input": subtask.get("input") or {},
            "requires_approval": bool(subtask.get("requires_approval", False)),
            "risk_level": subtask.get("risk_level", "low"),
        }

    def _heuristic_plan(self, goal: str) -> list[dict[str, Any]]:
        lowered = goal.lower()
        subtasks: list[dict[str, Any]] = []

        if any(word in lowered for word in ["research", "search", "find", "latest", "top"]):
            subtasks.append(
                {
                    "title": "Research source material",
                    "agent_name": "web_search",
                    "objective": goal,
                    "input": {"query": goal},
                    "requires_approval": False,
                    "risk_level": "low",
                }
            )

        if any(word in lowered for word in ["csv", "data", "table", "analysis", "compare", "stats"]):
            subtasks.append(
                {
                    "title": "Analyze structured findings",
                    "agent_name": "data_analysis",
                    "objective": "Turn collected information into structured observations.",
                    "input": {},
                    "requires_approval": False,
                    "risk_level": "low",
                }
            )

        if any(word in lowered for word in ["code", "script", "calculate", "pdf", "file", "save"]):
            subtasks.append(
                {
                    "title": "Prepare executable artifact",
                    "agent_name": "code_execution",
                    "objective": "Run a controlled Python snippet if the plan includes one.",
                    "input": {},
                    "requires_approval": True,
                    "risk_level": "medium",
                }
            )

        if not subtasks:
            subtasks.append(
                {
                    "title": "Investigate goal",
                    "agent_name": "web_search",
                    "objective": goal,
                    "input": {"query": goal},
                    "requires_approval": False,
                    "risk_level": "low",
                }
            )

        return subtasks[:6]

