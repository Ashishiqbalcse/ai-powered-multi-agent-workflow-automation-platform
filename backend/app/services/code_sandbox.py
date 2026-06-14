from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from app.core.config import get_settings


def run_python_snippet(code: str) -> dict[str, str | int | bool]:
    settings = get_settings()
    with tempfile.TemporaryDirectory(prefix="agent-code-") as tmp:
        snippet_path = Path(tmp) / "snippet.py"
        snippet_path.write_text(code, encoding="utf-8")
        try:
            result = subprocess.run(
                [sys.executable, "-I", str(snippet_path)],
                cwd=tmp,
                capture_output=True,
                text=True,
                timeout=settings.code_sandbox_timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            return {
                "ok": False,
                "exit_code": 124,
                "stdout": exc.stdout or "",
                "stderr": f"Timed out after {settings.code_sandbox_timeout_seconds}s",
            }

    return {
        "ok": result.returncode == 0,
        "exit_code": result.returncode,
        "stdout": result.stdout[-8000:],
        "stderr": result.stderr[-8000:],
    }

