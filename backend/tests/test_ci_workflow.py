from pathlib import Path


WORKFLOW_PATH = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "security-gate.yml"


def test_security_gate_workflow_exists() -> None:
    assert WORKFLOW_PATH.exists()


def test_security_gate_workflow_runs_required_commands() -> None:
    content = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "python -m pip install -r requirements.txt" in content
    assert "python -m alembic upgrade head" in content
    assert "python -m app.commands.seed_database" in content
    assert "python -m app.commands.check_security_gate" in content


def test_security_gate_workflow_targets_main_branch() -> None:
    content = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "push:" in content
    assert "pull_request:" in content
    assert "- main" in content


def test_security_gate_workflow_uses_python_312() -> None:
    content = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert 'python-version: "3.12"' in content
