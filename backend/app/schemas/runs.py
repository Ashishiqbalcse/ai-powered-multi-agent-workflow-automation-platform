from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TaskRunCreate(BaseModel):
    goal: str = Field(min_length=5, max_length=5000)
    budget_usd: float | None = Field(default=None, gt=0)
    max_iterations: int | None = Field(default=None, ge=1, le=25)


class ApprovalDecision(BaseModel):
    approved: bool
    note: str | None = Field(default=None, max_length=1000)


class SubTaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    run_id: str
    agent_name: str
    title: str
    status: str
    iteration: int
    input_json: dict[str, Any] | None
    output_json: dict[str, Any] | None
    error: str | None
    created_at: datetime
    updated_at: datetime


class AgentEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    run_id: str
    agent_name: str
    event_type: str
    message: str
    payload: dict[str, Any] | None
    created_at: datetime


class ApiCallRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    run_id: str
    agent_name: str
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    created_at: datetime


class TaskRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    goal: str
    status: str
    budget_usd: float
    cost_usd: float
    max_iterations: int
    iterations: int
    plan_json: dict[str, Any] | None
    approval_payload: dict[str, Any] | None
    result_json: dict[str, Any] | None
    error: str | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None


class TaskRunDetail(TaskRunRead):
    subtasks: list[SubTaskRead] = []
    events: list[AgentEventRead] = []
    api_calls: list[ApiCallRead] = []

