from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session


class AgentResult(BaseModel):
    agent_name: str
    summary: str
    data: dict[str, Any] = Field(default_factory=dict)
    requires_approval: bool = False
    approval_plan: dict[str, Any] | None = None


class BaseAgent(ABC):
    name: str

    @abstractmethod
    async def run(
        self,
        *,
        db: Session,
        run_id: str,
        subtask: dict[str, Any],
        context: dict[str, Any],
    ) -> AgentResult:
        raise NotImplementedError

