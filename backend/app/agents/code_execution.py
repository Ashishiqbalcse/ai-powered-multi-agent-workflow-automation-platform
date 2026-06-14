from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.agents.base import AgentResult, BaseAgent
from app.services.code_sandbox import run_python_snippet


class CodeExecutionAgent(BaseAgent):
    name = "code_execution"

    async def run(
        self,
        *,
        db: Session,
        run_id: str,
        subtask: dict[str, Any],
        context: dict[str, Any],
    ) -> AgentResult:
        code = subtask.get("input", {}).get("python")
        if not code:
            return AgentResult(
                agent_name=self.name,
                summary="No Python snippet was provided, so execution was skipped.",
                data={
                    "recommendation": (
                        "Have the orchestrator or an approved user provide input.python "
                        "for this agent to execute."
                    )
                },
            )

        output = run_python_snippet(code)
        status = "completed" if output["ok"] else "failed"
        return AgentResult(
            agent_name=self.name,
            summary=f"Python snippet {status} with exit code {output['exit_code']}.",
            data={"execution": output},
        )

