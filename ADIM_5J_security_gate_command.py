from __future__ import annotations

from pathlib import Path
import py_compile

ROOT_DIR = Path(r"C:\missio")
README_PATH = ROOT_DIR / "README.md"
SECURITY_CHECKLIST_PATH = ROOT_DIR / "docs" / "SECURITY_CHECKLIST.md"

FILES = {'backend/app/commands/check_security_gate.py': 'from __future__ import annotations\n\nimport subprocess\nimport sys\nfrom dataclasses import dataclass\n\n\n@dataclass(frozen=True)\nclass SecurityGateStep:\n    """Single security gate command step."""\n\n    name: str\n    command: list[str]\n\n\nSECURITY_GATE_STEPS: list[SecurityGateStep] = [\n    SecurityGateStep(\n        name="Baseline tablo kontrolü",\n        command=["python", "-m", "app.commands.check_baseline"],\n    ),\n    SecurityGateStep(\n        name="Production güvenlik ayar kontrolü",\n        command=["python", "-m", "app.commands.check_production_security"],\n    ),\n    SecurityGateStep(\n        name="Auth güvenlik temel kontrolü",\n        command=["python", "-m", "app.commands.check_auth_security"],\n    ),\n    SecurityGateStep(\n        name="JWT token güvenlik kontrolü",\n        command=["python", "-m", "app.commands.check_token_security"],\n    ),\n    SecurityGateStep(\n        name="Auth service kontrolü",\n        command=["python", "-m", "app.commands.check_auth_service"],\n    ),\n    SecurityGateStep(\n        name="Login brute-force ve audit log kontrolü",\n        command=["python", "-m", "app.commands.check_login_security"],\n    ),\n    SecurityGateStep(\n        name="Role ve business scope kontrolü",\n        command=["python", "-m", "app.commands.check_access_control"],\n    ),\n    SecurityGateStep(\n        name="Auth endpoint kontrolü",\n        command=["python", "-m", "app.commands.check_auth_endpoint"],\n    ),\n    SecurityGateStep(\n        name="API güvenlik kontrolü",\n        command=["python", "-m", "app.commands.check_api_security"],\n    ),\n    SecurityGateStep(\n        name="Rate limit kontrolü",\n        command=["python", "-m", "app.commands.check_rate_limit_security"],\n    ),\n]\n\nSECURITY_GATE_TEST_COMMAND = [\n    "python",\n    "-m",\n    "pytest",\n    "tests/test_security.py",\n    "tests/test_tokens.py",\n    "tests/test_auth_service.py",\n    "tests/test_login_security.py",\n    "tests/test_access_control.py",\n    "tests/test_auth_routes.py",\n    "tests/test_security_config.py",\n    "tests/test_api_security.py",\n    "tests/test_rate_limit.py",\n]\n\n\ndef run_command(command: list[str]) -> int:\n    """Run a command and stream output to the terminal."""\n\n    completed_process = subprocess.run(\n        command,\n        check=False,\n    )\n\n    return int(completed_process.returncode)\n\n\ndef run_security_gate_steps() -> list[tuple[SecurityGateStep, int]]:\n    """Run all security gate command steps."""\n\n    results: list[tuple[SecurityGateStep, int]] = []\n\n    for index, step in enumerate(SECURITY_GATE_STEPS, start=1):\n        print("")\n        print("=" * 80)\n        print(f"[{index}/{len(SECURITY_GATE_STEPS)}] {step.name}")\n        print("=" * 80)\n        print("Komut:", " ".join(step.command))\n\n        return_code = run_command(step.command)\n        results.append((step, return_code))\n\n        if return_code != 0:\n            print("")\n            print(f"BAŞARISIZ: {step.name}")\n            break\n\n    return results\n\n\ndef run_security_tests() -> int:\n    """Run security related pytest suite."""\n\n    print("")\n    print("=" * 80)\n    print("Güvenlik testleri")\n    print("=" * 80)\n    print("Komut:", " ".join(SECURITY_GATE_TEST_COMMAND))\n\n    return run_command(SECURITY_GATE_TEST_COMMAND)\n\n\ndef print_summary(\n    step_results: list[tuple[SecurityGateStep, int]],\n    test_return_code: int | None,\n) -> None:\n    """Print security gate summary."""\n\n    print("")\n    print("=" * 80)\n    print("Missio Güvenlik Kapısı Özeti")\n    print("=" * 80)\n\n    for step, return_code in step_results:\n        status = "OK" if return_code == 0 else "FAIL"\n        print(f"[{status}] {step.name}")\n\n    if test_return_code is not None:\n        test_status = "OK" if test_return_code == 0 else "FAIL"\n        print(f"[{test_status}] Güvenlik testleri")\n\n    print("=" * 80)\n\n\ndef main() -> None:\n    """Run Missio security gate checks and tests."""\n\n    print("Missio güvenlik kapısı kontrolü başlıyor.")\n    print("Bu komut, satış öncesi güvenlik temelini tek noktadan doğrular.")\n\n    step_results = run_security_gate_steps()\n\n    failed_step_exists = any(return_code != 0 for _, return_code in step_results)\n\n    if failed_step_exists:\n        print_summary(step_results=step_results, test_return_code=None)\n        print("Missio güvenlik kapısı başarısız.")\n        sys.exit(1)\n\n    test_return_code = run_security_tests()\n    print_summary(step_results=step_results, test_return_code=test_return_code)\n\n    if test_return_code != 0:\n        print("Missio güvenlik kapısı başarısız.")\n        sys.exit(1)\n\n    print("Missio güvenlik kapısı başarılı.")\n\n\nif __name__ == "__main__":\n    main()\n', 'backend/tests/test_security_gate.py': 'from app.commands import check_security_gate\n\n\ndef test_security_gate_contains_required_command_steps() -> None:\n    step_names = {step.name for step in check_security_gate.SECURITY_GATE_STEPS}\n\n    expected_names = {\n        "Baseline tablo kontrolü",\n        "Production güvenlik ayar kontrolü",\n        "Auth güvenlik temel kontrolü",\n        "JWT token güvenlik kontrolü",\n        "Auth service kontrolü",\n        "Login brute-force ve audit log kontrolü",\n        "Role ve business scope kontrolü",\n        "Auth endpoint kontrolü",\n        "API güvenlik kontrolü",\n        "Rate limit kontrolü",\n    }\n\n    assert expected_names.issubset(step_names)\n\n\ndef test_security_gate_test_command_contains_security_tests() -> None:\n    command_text = " ".join(check_security_gate.SECURITY_GATE_TEST_COMMAND)\n\n    assert "tests/test_security.py" in command_text\n    assert "tests/test_tokens.py" in command_text\n    assert "tests/test_auth_service.py" in command_text\n    assert "tests/test_login_security.py" in command_text\n    assert "tests/test_access_control.py" in command_text\n    assert "tests/test_auth_routes.py" in command_text\n    assert "tests/test_security_config.py" in command_text\n    assert "tests/test_api_security.py" in command_text\n    assert "tests/test_rate_limit.py" in command_text\n\n\ndef test_run_security_gate_steps_stops_on_failure(monkeypatch) -> None:\n    calls: list[list[str]] = []\n\n    def fake_run_command(command: list[str]) -> int:\n        calls.append(command)\n        return 1 if len(calls) == 2 else 0\n\n    monkeypatch.setattr(check_security_gate, "run_command", fake_run_command)\n\n    results = check_security_gate.run_security_gate_steps()\n\n    assert len(results) == 2\n    assert results[0][1] == 0\n    assert results[1][1] == 1\n', 'docs/SECURITY_GATE.md': '# Missio Security Gate\n\nBu doküman Missio güvenlik kapısı komutunu açıklar.\n\nGüvenlik kapısı; auth, token, brute-force, audit log, rol kontrolü, business scope, API güvenliği, rate limit ve production config kontrollerini tek noktadan çalıştırır.\n\n---\n\n## Komut\n\nBackend klasörü içinde çalıştırılır:\n\n```powershell\ncd C:\\missio\\backend\npython -m app.commands.check_security_gate\n```\n\n---\n\n## Kapsam\n\nBu komut şu kontrolleri çalıştırır:\n\n- Baseline tablo kontrolü\n- Production güvenlik ayar kontrolü\n- Auth güvenlik temel kontrolü\n- JWT token güvenlik kontrolü\n- Auth service kontrolü\n- Login brute-force ve audit log kontrolü\n- Role ve business scope kontrolü\n- Auth endpoint kontrolü\n- API güvenlik kontrolü\n- Rate limit kontrolü\n- Güvenlik odaklı pytest seti\n\n---\n\n## Kullanım Zamanı\n\nBu komut şu durumlarda çalıştırılmalıdır:\n\n- Yeni güvenlik değişikliğinden sonra\n- Auth veya kullanıcı sistemi değiştiğinde\n- Endpoint güvenlik davranışı değiştiğinde\n- Migration değişikliğinden sonra\n- Satışa hazırlık kontrolünden önce\n- Release öncesinde\n\n---\n\n## Başarı Kriteri\n\nKomut sonunda şu çıktı görülmelidir:\n\n```text\nMissio güvenlik kapısı başarılı.\n```\n\nBu çıktı yoksa ürün güvenlik kapısından geçmiş sayılmaz.\n\n---\n\n## Not\n\nBu komut local geliştirme ortamında çalışır.\n\nProduction kuruluma geçildiğinde ayrıca gerçek ortam değişkenleri, HTTPS, dosya yetkileri, backup/restore ve müşteri teslim kontrolleri yapılmalıdır.\n'}

README_INSERT = """
### Güvenlik Kapısı Komutu

Missio güvenlik kontrolleri tek komutla çalıştırılabilir:

```powershell
cd C:\\missio\\backend
python -m app.commands.check_security_gate
```

Bu komut auth, token, brute-force, audit log, rol kontrolü, business scope, API security, rate limit ve production config kontrollerini çalıştırır.

Detaylı doküman:

```text
docs/SECURITY_GATE.md
```
"""

CHECKLIST_APPEND = """
---

## 7. Güvenlik Kapısı Komutu

Missio güvenlik kapısı tek komutla çalıştırılır:

```powershell
cd C:\\missio\\backend
python -m app.commands.check_security_gate
```

Bu komut başarılı olmadan ürün satışa hazır kabul edilmez.
"""


def write_file(relative_path: str, content: str) -> None:
    target = ROOT_DIR / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    print(f"Yazildi: {target}")


def update_readme() -> None:
    if not README_PATH.exists():
        print("README.md bulunamadi, atlandi.")
        return

    content = README_PATH.read_text(encoding="utf-8")

    if "python -m app.commands.check_security_gate" in content:
        print("README.md guvenlik kapisi komutu zaten var, atlandi.")
        return

    marker = "Detaylı güvenlik kontrol listesi:"

    if marker in content:
        content = content.replace(marker, README_INSERT.strip() + "\n\n" + marker, 1)
    else:
        content = content.rstrip() + "\n\n" + README_INSERT.strip() + "\n"

    README_PATH.write_text(content, encoding="utf-8")
    print("README.md guncellendi.")


def update_security_checklist() -> None:
    if not SECURITY_CHECKLIST_PATH.exists():
        print("SECURITY_CHECKLIST.md bulunamadi, atlandi.")
        return

    content = SECURITY_CHECKLIST_PATH.read_text(encoding="utf-8")

    if "python -m app.commands.check_security_gate" not in content:
        content = content.rstrip() + "\n\n" + CHECKLIST_APPEND.strip() + "\n"

    SECURITY_CHECKLIST_PATH.write_text(content, encoding="utf-8")
    print("SECURITY_CHECKLIST.md guncellendi.")


def compile_files() -> None:
    for relative_path in FILES:
        if relative_path.endswith(".py"):
            py_compile.compile(str(ROOT_DIR / relative_path), doraise=True)

    print("Python syntax kontrolu basarili.")


def main() -> None:
    print("Missio ADIM 5J guvenlik kapisi genel dogrulama komutu olusturuluyor.")
    print("")

    for relative_path, content in FILES.items():
        write_file(relative_path, content)

    update_readme()
    update_security_checklist()
    compile_files()

    print("")
    print("Tamamlandi.")


if __name__ == "__main__":
    main()
