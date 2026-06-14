from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, get_db
from app.models.audit import AgentEvent
from app.schemas.runs import AgentEventRead, ApprovalDecision, TaskRunCreate, TaskRunDetail, TaskRunRead
from app.services.run_service import RunService
from app.services.websocket_manager import websocket_manager


router = APIRouter()
run_service = RunService()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/runs", response_model=TaskRunRead, status_code=201)
async def create_run(
    payload: TaskRunCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> TaskRunRead:
    run = run_service.create_run(db, payload)
    background_tasks.add_task(run_service.execute_run, run.id)
    return run


@router.get("/runs", response_model=list[TaskRunRead])
def list_runs(db: Session = Depends(get_db)) -> list[TaskRunRead]:
    return run_service.list_runs(db)


@router.get("/runs/{run_id}", response_model=TaskRunDetail)
def get_run(run_id: str, db: Session = Depends(get_db)) -> TaskRunDetail:
    run = run_service.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.get("/runs/{run_id}/events", response_model=list[AgentEventRead])
def get_run_events(run_id: str, db: Session = Depends(get_db)) -> list[AgentEventRead]:
    return (
        db.query(AgentEvent)
        .filter(AgentEvent.run_id == run_id)
        .order_by(AgentEvent.created_at)
        .all()
    )


@router.post("/runs/{run_id}/approval", response_model=TaskRunRead)
async def decide_approval(
    run_id: str,
    decision: ApprovalDecision,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> TaskRunRead:
    run = run_service.record_approval(db, run_id, decision)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    if decision.approved:
        background_tasks.add_task(run_service.execute_run, run_id)
    return run


@router.websocket("/ws/runs/{run_id}")
async def stream_run(websocket: WebSocket, run_id: str) -> None:
    await websocket_manager.connect(run_id, websocket)
    db = SessionLocal()
    try:
        events = (
            db.query(AgentEvent)
            .filter(AgentEvent.run_id == run_id)
            .order_by(AgentEvent.created_at)
            .all()
        )
        await websocket.send_json(
            jsonable_encoder(
                {
                    "type": "event_history",
                    "events": [AgentEventRead.model_validate(event).model_dump() for event in events],
                }
            )
        )
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect(run_id, websocket)
    finally:
        db.close()

