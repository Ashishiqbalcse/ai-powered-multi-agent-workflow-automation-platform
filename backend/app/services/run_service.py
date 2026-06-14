from __future__ import annotations

import asyncio
from datetime import timezone
from typing import Any

from sqlalchemy import desc
from sqlalchemy.orm import Session, selectinload

from app.agents.base import BaseAgent
from app.agents.code_execution import CodeExecutionAgent
from app.agents.data_analysis import DataAnalysisAgent
from app.agents.orchestrator import OrchestratorAgent
from app.agents.synthesizer import ResultSynthesizer
from app.agents.web_search import WebSearchAgent
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.audit import AgentEvent, RunStatus, SubTask, SubTaskStatus, TaskRun, utc_now
from app.schemas.runs import ApprovalDecision, TaskRunCreate
from app.services.memory import MemoryService
from app.services.websocket_manager import WebSocketManager, websocket_manager


class RunService:
    def __init__(self, manager: WebSocketManager = websocket_manager) -> None:
        self.settings = get_settings()
        self.manager = manager
        self.orchestrator = OrchestratorAgent()
        self.synthesizer = ResultSynthesizer()
        self.agents: dict[str, BaseAgent] = {
            WebSearchAgent.name: WebSearchAgent(),
            CodeExecutionAgent.name: CodeExecutionAgent(),
            DataAnalysisAgent.name: DataAnalysisAgent(),
        }

    def create_run(self, db: Session, payload: TaskRunCreate) -> TaskRun:
        run = TaskRun(
            goal=payload.goal,
            budget_usd=payload.budget_usd or self.settings.default_budget_usd,
            max_iterations=payload.max_iterations or self.settings.max_iterations,
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    def list_runs(self, db: Session, limit: int = 50) -> list[TaskRun]:
        return db.query(TaskRun).order_by(desc(TaskRun.created_at)).limit(limit).all()

    def get_run(self, db: Session, run_id: str) -> TaskRun | None:
        return (
            db.query(TaskRun)
            .options(
                selectinload(TaskRun.subtasks),
                selectinload(TaskRun.events),
                selectinload(TaskRun.api_calls),
            )
            .filter(TaskRun.id == run_id)
            .first()
        )

    def record_approval(
        self, db: Session, run_id: str, decision: ApprovalDecision
    ) -> TaskRun | None:
        run = db.get(TaskRun, run_id)
        if not run:
            return None

        payload = run.approval_payload or {}
        payload.update(
            {
                "approved": decision.approved,
                "note": decision.note,
                "decided_at": utc_now().isoformat(),
            }
        )
        run.approval_payload = payload

        if decision.approved:
            run.status = RunStatus.QUEUED.value
        else:
            run.status = RunStatus.STOPPED.value
            run.completed_at = utc_now()
        db.commit()
        db.refresh(run)
        return run

    async def execute_run(self, run_id: str) -> None:
        db = SessionLocal()
        try:
            run = db.get(TaskRun, run_id)
            if not run or run.status in {RunStatus.COMPLETED.value, RunStatus.STOPPED.value}:
                return

            await self._mark_run_running(db, run)
            subtasks = await self._ensure_plan(db, run)
            if self._requires_approval(run, subtasks):
                await self._pause_for_approval(db, run, subtasks)
                return

            context: dict[str, Any] = {"goal": run.goal, "results": []}
            memory = MemoryService(db)

            for index, subtask in enumerate(subtasks):
                db.refresh(run)
                if await self._should_stop_for_limits(db, run, index):
                    return

                agent_name = subtask["agent_name"]
                agent = self.agents.get(agent_name)
                if not agent:
                    await self._emit(
                        db,
                        run.id,
                        "orchestrator",
                        "agent_missing",
                        f"No registered agent named {agent_name}.",
                        {"subtask": subtask},
                    )
                    continue

                subtask_row = self._create_subtask(db, run.id, index, subtask)
                await self._emit(
                    db,
                    run.id,
                    agent_name,
                    "agent_started",
                    subtask["title"],
                    {"subtask_id": subtask_row.id, "subtask": subtask},
                )

                try:
                    result = await asyncio.wait_for(
                        agent.run(db=db, run_id=run.id, subtask=subtask, context=context),
                        timeout=self.settings.agent_timeout_seconds,
                    )
                except Exception as exc:  # noqa: BLE001
                    subtask_row.status = SubTaskStatus.FAILED.value
                    subtask_row.error = str(exc)
                    run.status = RunStatus.FAILED.value
                    run.error = str(exc)
                    run.completed_at = utc_now()
                    db.commit()
                    await self._emit(
                        db,
                        run.id,
                        agent_name,
                        "agent_failed",
                        str(exc),
                        {"subtask_id": subtask_row.id},
                    )
                    return

                result_payload = result.model_dump()
                subtask_row.status = SubTaskStatus.COMPLETED.value
                subtask_row.output_json = result_payload
                run.iterations = index + 1
                db.commit()

                context["results"].append(result_payload)
                memory.remember(
                    agent_name=agent_name,
                    run_id=run.id,
                    key=subtask["title"],
                    text=result.summary,
                    metadata={"subtask_id": subtask_row.id, "iteration": index + 1},
                )
                await self._emit(
                    db,
                    run.id,
                    agent_name,
                    "agent_completed",
                    result.summary,
                    {"subtask_id": subtask_row.id, "result": result_payload},
                )

            final = await self.synthesizer.synthesize(
                db=db,
                run_id=run.id,
                goal=run.goal,
                results=context["results"],
            )
            run.result_json = final
            run.status = RunStatus.COMPLETED.value
            run.completed_at = utc_now()
            db.commit()

            await self._emit(
                db,
                run.id,
                "result_synthesizer",
                "run_completed",
                final.get("summary", "Run completed."),
                {"result": final},
            )
        except Exception as exc:  # noqa: BLE001
            run = db.get(TaskRun, run_id)
            if run:
                run.status = RunStatus.FAILED.value
                run.error = str(exc)
                run.completed_at = utc_now()
                db.commit()
            await self._emit(
                db,
                run_id,
                "orchestrator",
                "run_failed",
                str(exc),
                {"error": str(exc)},
            )
        finally:
            db.close()

    async def _mark_run_running(self, db: Session, run: TaskRun) -> None:
        run.status = RunStatus.RUNNING.value
        db.commit()
        await self._emit(
            db,
            run.id,
            "orchestrator",
            "run_started",
            "Workflow execution started.",
            {"goal": run.goal},
        )

    async def _ensure_plan(self, db: Session, run: TaskRun) -> list[dict[str, Any]]:
        if run.plan_json and run.plan_json.get("subtasks"):
            return run.plan_json["subtasks"]

        subtasks = await self.orchestrator.plan(db=db, run_id=run.id, goal=run.goal)
        run.plan_json = {"subtasks": subtasks}
        db.commit()
        await self._emit(
            db,
            run.id,
            "orchestrator",
            "plan_created",
            f"Created {len(subtasks)} subtask(s).",
            {"subtasks": subtasks},
        )
        return subtasks

    def _requires_approval(self, run: TaskRun, subtasks: list[dict[str, Any]]) -> bool:
        approved = bool((run.approval_payload or {}).get("approved"))
        return not approved and any(task.get("requires_approval") for task in subtasks)

    async def _pause_for_approval(
        self, db: Session, run: TaskRun, subtasks: list[dict[str, Any]]
    ) -> None:
        risky = [task for task in subtasks if task.get("requires_approval")]
        run.status = RunStatus.WAITING_APPROVAL.value
        run.approval_payload = {
            "approved": False,
            "reason": "One or more subtasks require human approval before execution.",
            "subtasks": risky,
            "requested_at": utc_now().astimezone(timezone.utc).isoformat(),
        }
        db.commit()
        await self._emit(
            db,
            run.id,
            "approval_gate",
            "approval_required",
            "Human approval is required before continuing.",
            run.approval_payload,
        )

    async def _should_stop_for_limits(self, db: Session, run: TaskRun, index: int) -> bool:
        if index >= run.max_iterations:
            run.status = RunStatus.FAILED.value
            run.error = "Maximum iteration count reached."
            run.completed_at = utc_now()
            db.commit()
            await self._emit(
                db,
                run.id,
                "orchestrator",
                "iteration_limit",
                "Maximum iteration count reached.",
                {"max_iterations": run.max_iterations},
            )
            return True

        if run.cost_usd >= run.budget_usd:
            run.status = RunStatus.FAILED.value
            run.error = "Budget cap reached."
            run.completed_at = utc_now()
            db.commit()
            await self._emit(
                db,
                run.id,
                "cost_tracker",
                "budget_exhausted",
                "Budget cap reached.",
                {"budget_usd": run.budget_usd, "cost_usd": run.cost_usd},
            )
            return True

        if run.cost_usd >= run.budget_usd * self.settings.cost_warn_threshold:
            await self._emit(
                db,
                run.id,
                "cost_tracker",
                "budget_warning",
                "Run has crossed the budget warning threshold.",
                {"budget_usd": run.budget_usd, "cost_usd": run.cost_usd},
            )
        return False

    def _create_subtask(
        self, db: Session, run_id: str, index: int, subtask: dict[str, Any]
    ) -> SubTask:
        row = SubTask(
            run_id=run_id,
            agent_name=subtask["agent_name"],
            title=subtask["title"],
            status=SubTaskStatus.RUNNING.value,
            iteration=index + 1,
            input_json=subtask,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    async def _emit(
        self,
        db: Session,
        run_id: str,
        agent_name: str,
        event_type: str,
        message: str,
        payload: dict[str, Any] | None = None,
    ) -> AgentEvent:
        event = AgentEvent(
            run_id=run_id,
            agent_name=agent_name,
            event_type=event_type,
            message=message,
            payload=payload or {},
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        await self.manager.broadcast(
            run_id,
            {
                "type": "agent_event",
                "event": {
                    "id": event.id,
                    "run_id": event.run_id,
                    "agent_name": event.agent_name,
                    "event_type": event.event_type,
                    "message": event.message,
                    "payload": event.payload,
                    "created_at": event.created_at,
                },
            },
        )
        return event

