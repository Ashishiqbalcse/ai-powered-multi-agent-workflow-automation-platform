from __future__ import annotations

from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.agents.base import AgentResult, BaseAgent
from app.core.config import get_settings
from app.services.memory import MemoryService


class WebSearchAgent(BaseAgent):
    name = "web_search"

    async def run(
        self,
        *,
        db: Session,
        run_id: str,
        subtask: dict[str, Any],
        context: dict[str, Any],
    ) -> AgentResult:
        settings = get_settings()

        print("DEBUG TAVILY:", settings.tavily_api_key)
        print("DEBUG SERPER:", settings.serper_api_key)

        query = (
            subtask.get("input", {}).get("query")
            or subtask.get("objective")
            or context["goal"]
        )

        memory = MemoryService(db).recall(
            agent_name=self.name,
            query=query,
        )

        if settings.tavily_api_key:
            results = await self._search_tavily(
                query,
                settings.tavily_api_key,
            )
        elif settings.serper_api_key:
            results = await self._search_serper(
                query,
                settings.serper_api_key,
            )
        else:
            results = [
                {
                    "title": "Search provider not configured",
                    "url": "",
                    "snippet": "Set TAVILY_API_KEY or SERPER_API_KEY to enable live web search.",
                }
            ]

        summary = self._summarize(
            query,
            results,
            memory,
        )

        return AgentResult(
            agent_name=self.name,
            summary=summary,
            data={
                "query": query,
                "results": results,
                "memory": memory,
            },
        )

    async def _search_tavily(
        self,
        query: str,
        api_key: str,
    ) -> list[dict[str, str]]:
        print("USING TAVILY")
        print("QUERY:", query)

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": api_key,
                    "query": query,
                    "max_results": 5,
                },
            )

            print("STATUS:", response.status_code)
            print("BODY:", response.text)

            response.raise_for_status()

        payload = response.json()

        return [
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("content", ""),
            }
            for item in payload.get("results", [])
        ]

    async def _search_serper(
        self,
        query: str,
        api_key: str,
    ) -> list[dict[str, str]]:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                "https://google.serper.dev/search",
                headers={
                    "X-API-KEY": api_key,
                    "Content-Type": "application/json",
                },
                json={
                    "q": query,
                    "num": 5,
                },
            )

            response.raise_for_status()

        payload = response.json()
        organic = payload.get("organic", [])

        return [
            {
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "snippet": item.get("snippet", ""),
            }
            for item in organic
        ]

    def _summarize(
        self,
        query: str,
        results: list[dict[str, str]],
        memory: list[dict[str, Any]],
    ) -> str:
        if not results:
            return f"No search results found for `{query}`."

        memory_note = (
            f" Reused {len(memory)} memory item(s)."
            if memory
            else ""
        )

        top_titles = ", ".join(
            item["title"]
            for item in results[:3]
            if item.get("title")
        )

        return (
            f"Found {len(results)} result(s) for `{query}`. "
            f"Top signals: {top_titles}.{memory_note}"
        )