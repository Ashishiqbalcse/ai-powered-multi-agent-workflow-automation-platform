from __future__ import annotations

from io import StringIO
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from app.agents.base import AgentResult, BaseAgent


class DataAnalysisAgent(BaseAgent):
    name = "data_analysis"

    async def run(
        self,
        *,
        db: Session,
        run_id: str,
        subtask: dict[str, Any],
        context: dict[str, Any],
    ) -> AgentResult:
        input_payload = subtask.get("input", {})
        frame = self._load_dataframe(input_payload)

        if frame is None:
            findings = context.get("results", [])
            return AgentResult(
                agent_name=self.name,
                summary=f"Structured {len(findings)} prior result(s); no CSV was supplied.",
                data={
                    "rows": len(findings),
                    "chart_recommendations": [
                        "Use a comparison table for qualitative attributes.",
                        "Use a bar chart for numeric scores or counts once available.",
                    ],
                },
            )

        stats = frame.describe(include="all").fillna("").to_dict()
        chart_recommendations = self._recommend_charts(frame)
        return AgentResult(
            agent_name=self.name,
            summary=f"Analyzed {len(frame)} row(s) and {len(frame.columns)} column(s).",
            data={
                "columns": list(frame.columns),
                "row_count": len(frame),
                "stats": stats,
                "chart_recommendations": chart_recommendations,
            },
        )

    def _load_dataframe(self, input_payload: dict[str, Any]) -> pd.DataFrame | None:
        if input_payload.get("csv_text"):
            return pd.read_csv(StringIO(input_payload["csv_text"]))

        if input_payload.get("csv_path"):
            path = Path(input_payload["csv_path"]).expanduser()
            if path.exists() and path.is_file():
                return pd.read_csv(path)

        rows = input_payload.get("rows")
        if isinstance(rows, list) and rows:
            return pd.DataFrame(rows)

        return None

    def _recommend_charts(self, frame: pd.DataFrame) -> list[str]:
        numeric = frame.select_dtypes(include="number").columns.tolist()
        categorical = frame.select_dtypes(exclude="number").columns.tolist()
        recommendations: list[str] = []
        if numeric and categorical:
            recommendations.append(f"Bar chart: {categorical[0]} by {numeric[0]}")
        if len(numeric) >= 2:
            recommendations.append(f"Scatter plot: {numeric[0]} vs {numeric[1]}")
        if categorical:
            recommendations.append(f"Count plot: distribution of {categorical[0]}")
        return recommendations or ["Summary table"]

