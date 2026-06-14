from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.config import get_settings


class LLMClient:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()

    async def complete_json(
        self,
        *,
        run_id: str,
        agent_name: str,
        system_prompt: str,
        user_prompt: str,
        fallback: dict[str, Any],
    ) -> dict[str, Any]:
        print("LLM disabled for cloud deployment. Returning fallback response.")
        return fallback