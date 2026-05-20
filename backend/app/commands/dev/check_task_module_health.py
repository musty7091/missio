from __future__ import annotations

import subprocess
import sys
import time
from dataclasses import dataclass

from app.core.config import settings


@dataclass(frozen=True)
class HealthCheckStep:
    """Single health check step."""

    title: str
    command: list[str]


SAFE_HEALTH_CHECK_ENVIRONMENTS = {
    "local",
    "dev",
    "development",
    "test",
    "testing",
}


HEALTH_CHECK_STEPS = [
    HealthCheckStep(
        title="Task route import kontrolü",
        command=[
            sys.executable,
            "-c",
            "from app.api.routes.tasks import router; from app.main import app; print('task route import başarılı')",
        ],
    ),
    HealthCheckStep(
        title="Task attachment service import kontrolü",
        command=[
            sys.executable,
            "-c",
            "from app.services.task_attachment_service import upload_task_attachment, list_task_attachments, delete_task_attachment; print('task attachment service import başarılı')",
        ],
    ),
    HealthCheckStep(
        title="Demo görev ekranı akışı",
        command=[
            sys.executable,
            "-m",
            "app.commands.dev.check_task_demo_flow",
        ],
    ),
    HealthCheckStep(
        title="Görev yaşam döngüsü akışı",
        command=[
            sys.executable,
            "-m",
            "app.commands.dev.check_task_lifecycle_flow",
        ],
    ),
    HealthCheckStep(
        title="Görev geçmişi endpoint akışı",
        command=[
            sys.executable,
            "-m",
            "app.commands.dev.check_task_event_endpoint_flow",
        ],
    ),
    HealthCheckStep(
        title="Fotoğraf yükleme/listeleme/silme endpoint akışı",
        command=[
            sys.executable,
            "-m",
            "app.commands.dev.check_task_attachment_endpoint_flow",
        ],
    ),
    HealthCheckStep(
        title="Fotoğraf görüntüleme endpoint akışı",
        command=[
            sys.executable,
            "-m",
            "app.commands.dev.check_task_attachment_file_endpoint_flow",
        ],
    ),
    HealthCheckStep(
        title="Fotoğraf yetki kontrolü akışı",
        command=[
            sys.executable,
            "-m",
            "app.commands.dev.check_task_attachment_access_control_flow",
        ],
    ),
    HealthCheckStep(
        title="Fotoğraf temizlik politikası akışı",
        command=[
            sys.executable,
            "-m",
            "app.commands.dev.check_task_attachment_cleanup_flow",
        ],
    ),
    HealthCheckStep(
        title="Fotoğraf zorunlu görev tamamlama akışı",
        command=[
            sys.executable,
            "-m",
            "app.commands.dev.check_task_photo_required_completion_flow",
        ],
    ),
    HealthCheckStep(
        title="Konum zorunlu görev akışı",
        command=[
            sys.executable,
            "-m",
            "app.commands.dev.check_task_location_required_flow",
        ],
    ),
    HealthCheckStep(
        title="Eski fotoğraf temizleme komutu dry-run",
        command=[
            sys.executable,
            "-m",
            "app.commands.cleanup_old_task_attachments",
        ],
    ),
]


def ensure_health_check_environment_is_safe() -> None:
    """Block demo/test health checks in production-like environments."""

    environment = settings.environment.strip().lower()

    if environment in SAFE_HEALTH_CHECK_ENVIRONMENTS:
        return

    raise RuntimeError(
        "Görev modülü sağlık kontrolü production benzeri ortamda çalıştırılamaz. "
        f"Mevcut MISSIO_ENVIRONMENT={settings.environment!r}. "
        "Bu komut sadece local/dev/test ortamlarında çalıştırılmalıdır."
    )


def run_step(step_number: int, total_steps: int, step: HealthCheckStep) -> None:
    """Run one health check step."""

    print("")
    print("=" * 80)
    print(f"[STEP {step_number}/{total_steps}] {step.title}")
    print("=" * 80)
    print("[COMMAND] " + " ".join(step.command))

    started_at = time.perf_counter()

    completed_process = subprocess.run(
        step.command,
        check=False,
        text=True,
    )

    elapsed_seconds = time.perf_counter() - started_at

    if completed_process.returncode != 0:
        print("")
        print(
            f"[FAIL] {step.title} başarısız. "
            f"returncode={completed_process.returncode}, "
            f"elapsed={elapsed_seconds:.2f}s"
        )
        raise SystemExit(completed_process.returncode)

    print("")
    print(f"[OK] {step.title} başarılı. elapsed={elapsed_seconds:.2f}s")


def main() -> None:
    """Run Missio task module health checks."""

    ensure_health_check_environment_is_safe()

    total_steps = len(HEALTH_CHECK_STEPS)
    started_at = time.perf_counter()

    print("[INFO] Missio görev modülü genel sağlık kontrolü başladı.")
    print(f"[INFO] Ortam: MISSIO_ENVIRONMENT={settings.environment}")
    print(f"[INFO] Toplam kontrol adımı: {total_steps}")
    print("[INFO] Herhangi bir adım başarısız olursa komut orada durur.")
    print("")
    print("[INFO] Ön koşul:")
    print("       Demo veri yoksa önce şu komutu local izinle çalıştırın:")
    print("       PowerShell: $env:MISSIO_ALLOW_DEMO_SEED='1'")
    print("       python -m app.commands.dev.seed_local_task_demo_data")
    print("       Remove-Item Env:\\MISSIO_ALLOW_DEMO_SEED -ErrorAction SilentlyContinue")

    for index, step in enumerate(HEALTH_CHECK_STEPS, start=1):
        run_step(
            step_number=index,
            total_steps=total_steps,
            step=step,
        )

    elapsed_seconds = time.perf_counter() - started_at

    print("")
    print("=" * 80)
    print("[OK] Missio görev modülü genel sağlık kontrolü başarılı.")
    print(f"[OK] Toplam süre: {elapsed_seconds:.2f}s")
    print("=" * 80)


if __name__ == "__main__":
    main()