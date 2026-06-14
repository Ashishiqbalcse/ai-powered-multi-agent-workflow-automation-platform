from __future__ import annotations

import json
from typing import Any

from ollama import AsyncClient
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

        try:
            client = AsyncClient(host="http://127.0.0.1:11434")

            response = await client.chat(
                model="qwen2.5:0.5b",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            system_prompt
                            + "\n\nReturn ONLY valid JSON. "
                            "Do not include markdown, code fences, or explanations."
                        ),
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
            )

            print("OLLAMA RESPONSE:", response)

            content = response.message.content

            print("OLLAMA CONTENT:", content)

            try:
                return json.loads(content)

            except json.JSONDecodeError:
                print("JSON PARSE FAILED")
                return fallback | {
                    "raw_response": content,
                }

        except Exception as e:
            print("OLLAMA ERROR:", str(e))
            return fallback | {
                "error": str(e),
            }