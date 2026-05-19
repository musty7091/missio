from app.commands import check_security_gate


def test_security_gate_contains_required_command_steps() -> None:
    step_names = {step.name for step in check_security_gate.SECURITY_GATE_STEPS}

    expected_names = {
        "Baseline tablo kontrolü",
        "Production güvenlik ayar kontrolü",
        "Auth güvenlik temel kontrolü",
        "JWT token güvenlik kontrolü",
        "Auth service kontrolü",
        "Login brute-force ve audit log kontrolü",
        "Role ve business scope kontrolü",
        "Auth endpoint kontrolü",
        "API güvenlik kontrolü",
        "Rate limit kontrolü",
    }

    assert expected_names.issubset(step_names)


def test_security_gate_uses_current_python_executable() -> None:
    command = check_security_gate.build_module_command("app.commands.check_baseline")

    assert command[0] == check_security_gate.sys.executable
    assert command[1:] == ["-m", "app.commands.check_baseline"]


def test_security_gate_pytest_command_uses_current_python_executable() -> None:
    command = check_security_gate.build_pytest_command()

    assert command[0] == check_security_gate.sys.executable
    assert command[1:3] == ["-m", "pytest"]


def test_security_gate_test_command_contains_security_tests() -> None:
    command_text = " ".join(check_security_gate.build_pytest_command())

    assert "tests/test_security.py" in command_text
    assert "tests/test_tokens.py" in command_text
    assert "tests/test_auth_service.py" in command_text
    assert "tests/test_login_security.py" in command_text
    assert "tests/test_access_control.py" in command_text
    assert "tests/test_auth_routes.py" in command_text
    assert "tests/test_security_config.py" in command_text
    assert "tests/test_api_security.py" in command_text
    assert "tests/test_rate_limit.py" in command_text


def test_run_security_gate_steps_stops_on_failure(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run_command(command: list[str]) -> int:
        calls.append(command)
        return 1 if len(calls) == 2 else 0

    monkeypatch.setattr(check_security_gate, "run_command", fake_run_command)

    results = check_security_gate.run_security_gate_steps()

    assert len(results) == 2
    assert results[0][1] == 0
    assert results[1][1] == 1
