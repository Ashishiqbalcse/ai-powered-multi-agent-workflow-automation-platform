from app.services.code_sandbox import run_python_snippet


def test_python_snippet_runs_in_isolated_subprocess() -> None:
    result = run_python_snippet("print(2 + 2)")

    assert result["ok"] is True
    assert result["exit_code"] == 0
    assert result["stdout"].strip() == "4"

