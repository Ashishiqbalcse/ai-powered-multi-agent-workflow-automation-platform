from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.services.llm import LLMClient


class ResultSynthesizer:
    name = "result_synthesizer"

    async def synthesize(
        self,
        *,
        db: Session,
        run_id: str,
        goal: str,
        results: list[dict[str, Any]],
    ) -> dict[str, Any]:
        fallback = {
            "summary": self._fallback_summary(results),
            "results": results,
            "next_actions": ["Review the audit log and approve any follow-up execution steps."],
        }
        llm = LLMClient(db)
        return await llm.complete_json(
            run_id=run_id,
            agent_name=self.name,
            system_prompt=(
                "You synthesize multi-agent task outputs into concise JSON. Return JSON only "
                "with summary, key_findings, gaps, next_actions, and artifacts."
            ),
            user_prompt=f"Goal: {goal}\nAgent results: {results}",
            fallback=fallback,
        )

    def _fallback_summary(self, results: list[dict[str, Any]]) -> str:
        if not results:
            return "No agent results were produced."
        return " ".join(result.get("summary", "") for result in results if result.get("summary"))

