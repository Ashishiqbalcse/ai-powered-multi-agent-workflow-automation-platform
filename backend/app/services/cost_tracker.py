from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.audit import ApiCallLog, TaskRun


# Conservative defaults for local estimates. Override in production if pricing changes.
MODEL_PRICING_USD_PER_1K = {
    "gpt-4.1-mini": {"input": 0.0004, "output": 0.0016},
    "gpt-4.1": {"input": 0.005, "output": 0.015},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
}


def estimate_cost_usd(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    pricing = MODEL_PRICING_USD_PER_1K.get(model, MODEL_PRICING_USD_PER_1K["gpt-4.1-mini"])
    return round(
        (prompt_tokens / 1000) * pricing["input"]
        + (completion_tokens / 1000) * pricing["output"],
        6,
    )


def log_api_call(
    db: Session,
    *,
    run_id: str,
    agent_name: str,
    provider: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> ApiCallLog:
    total_tokens = prompt_tokens + completion_tokens
    cost_usd = estimate_cost_usd(model, prompt_tokens, completion_tokens)
    record = ApiCallLog(
        run_id=run_id,
        agent_name=agent_name,
        provider=provider,
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        cost_usd=cost_usd,
    )
    db.add(record)

    run = db.get(TaskRun, run_id)
    if run:
        run.cost_usd = round((run.cost_usd or 0) + cost_usd, 6)

    db.commit()
    db.refresh(record)
    return record

