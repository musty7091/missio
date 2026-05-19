from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class SecurityGateStep:
    """Single security gate command step."""

    name: str
    module_name: str


SECURITY_GATE_STEPS: list[SecurityGateStep] = [
    SecurityGateStep(
        name="Dependency health kontrolü",
        module_name="app.commands.check_dependency_health",
    ),
    SecurityGateStep(
        name="Baseline tablo kontrolü",
        module_name="app.commands.check_baseline",
    ),
    SecurityGateStep(
        name="Production güvenlik ayar kontrolü",
        module_name="app.commands.check_production_security",
    ),
    SecurityGateStep(
        name="Auth güvenlik temel kontrolü",
        module_name="app.commands.check_auth_security",
    ),
    SecurityGateStep(
        name="JWT token güvenlik kontrolü",
        module_name="app.commands.check_token_security",
    ),
    SecurityGateStep(
        name="Auth service kontrolü",
        module_name="app.commands.check_auth_service",
    ),
    SecurityGateStep(
        name="Login brute-force ve audit log kontrolü",
        module_name="app.commands.check_login_security",
    ),
    SecurityGateStep(
        name="Role ve business scope kontrolü",
        module_name="app.commands.check_access_control",
    ),
    SecurityGateStep(
        name="Auth endpoint kontrolü",
        module_name="app.commands.check_auth_endpoint",
    ),
    SecurityGateStep(
        name="API güvenlik kontrolü",
        module_name="app.commands.check_api_security",
    ),
    SecurityGateStep(
        name="Rate limit kontrolü",
        module_name="app.commands.check_rate_limit_security",
    ),
]

SECURITY_TEST_PATHS = [
    "tests/test_security.py",
    "tests/test_tokens.py",
    "tests/test_auth_service.py",
    "tests/test_login_security.py",
    "tests/test_access_control.py",
    "tests/test_auth_routes.py",
    "tests/test_security_config.py",
    "tests/test_api_security.py",
    "tests/test_rate_limit.py",
    "tests/test_security_gate.py",
    "tests/test_dependency_health.py",
]


def build_module_command(module_name: str) -> list[str]:
    """Build command using the active Python interpreter."""

    return [sys.executable, "-m", module_name]


def build_pytest_command() -> list[str]:
    """Build pytest command using the active Python interpreter."""

    return [sys.executable, "-m", "pytest", *SECURITY_TEST_PATHS]


def run_command(command: list[str]) -> int:
    """Run a command and stream output to the terminal."""

    completed_process = subprocess.run(
        command,
        check=False,
    )

    return int(completed_process.returncode)


def run_security_gate_steps() -> list[tuple[SecurityGateStep, int]]:
    """Run all security gate command steps."""

    results: list[tuple[SecurityGateStep, int]] = []

    for index, step in enumerate(SECURITY_GATE_STEPS, start=1):
        command = build_module_command(step.module_name)

        print("")
        print("=" * 80)
        print(f"[{index}/{len(SECURITY_GATE_STEPS)}] {step.name}")
        print("=" * 80)
        print("Python:", sys.executable)
        print("Komut:", " ".join(command))

        return_code = run_command(command)
        results.append((step, return_code))

        if return_code != 0:
            print("")
            print(f"BAŞARISIZ: {step.name}")
            break

    return results


def run_security_tests() -> int:
    """Run security related pytest suite."""

    command = build_pytest_command()

    print("")
    print("=" * 80)
    print("Güvenlik testleri")
    print("=" * 80)
    print("Python:", sys.executable)
    print("Komut:", " ".join(command))

    return run_command(command)


def print_summary(
    step_results: list[tuple[SecurityGateStep, int]],
    test_return_code: int | None,
) -> None:
    """Print security gate summary."""

    print("")
    print("=" * 80)
    print("Missio Güvenlik Kapısı Özeti")
    print("=" * 80)

    for step, return_code in step_results:
        status = "OK" if return_code == 0 else "FAIL"
        print(f"[{status}] {step.name}")

    if test_return_code is not None:
        test_status = "OK" if test_return_code == 0 else "FAIL"
        print(f"[{test_status}] Güvenlik testleri")

    print("=" * 80)


def main() -> None:
    """Run Missio security gate checks and tests."""

    print("Missio güvenlik kapısı kontrolü başlıyor.")
    print("Bu komut, satış öncesi güvenlik temelini tek noktadan doğrular.")
    print(f"Aktif Python yorumlayıcısı: {sys.executable}")

    step_results = run_security_gate_steps()

    failed_step_exists = any(return_code != 0 for _, return_code in step_results)

    if failed_step_exists:
        print_summary(step_results=step_results, test_return_code=None)
        print("Missio güvenlik kapısı başarısız.")
        sys.exit(1)

    test_return_code = run_security_tests()
    print_summary(step_results=step_results, test_return_code=test_return_code)

    if test_return_code != 0:
        print("Missio güvenlik kapısı başarısız.")
        sys.exit(1)

    print("Missio güvenlik kapısı başarılı.")


if __name__ == "__main__":
    main()
