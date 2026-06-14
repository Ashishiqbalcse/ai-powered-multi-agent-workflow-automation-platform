from __future__ import annotations

from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    run_id: str
    goal: str
    subtasks: list[dict[str, Any]]
    results: list[dict[str, Any]]
    summary: str
    requires_approval: bool
    approval_plan: dict[str, Any]
    iteration: int
    budget_usd: float
    cost_usd: float
    errors: list[str]

