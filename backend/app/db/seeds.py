from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.app_setting import AppSetting
from app.models.module import Module
from app.models.package import Package


PACKAGE_DEFINITIONS: list[dict[str, object]] = [
    {
        "code": "starter",
        "name": "Başlangıç Paketi",
        "description": (
            "Patron paneli, personel girişi, görev oluşturma, görev atama, "
            "temel işlem geçmişi ve günlük görev özeti."
        ),
        "max_staff_count": 5,
    },
    {
        "code": "pro",
        "name": "Pro Paket",
        "description": (
            "Konumlu işlem kaydı, fotoğraflı görev kanıtı, görev şablonları, "
            "açılış/kapanış kontrol listeleri ve personel performans raporu."
        ),
        "max_staff_count": 15,
    },
    {
        "code": "field",
        "name": "Saha Paketi",
        "description": (
            "Saha görevleri, müşteri/teslimat lokasyonu, harita üzerinde işlem "
            "noktaları ve günlük saha performans raporu."
        ),
        "max_staff_count": 25,
    },
]

MODULE_DEFINITIONS: list[dict[str, str]] = [
    {
        "code": "task_core",
        "name": "Görev Merkezi",
        "description": "Görev oluşturma, atama ve durum takibi.",
    },
    {
        "code": "staff_panel",
        "name": "Personel Paneli",
        "description": "Personelin mobil öncelikli görev ekranı.",
    },
    {
        "code": "location_logs",
        "name": "Konumlu İşlem Kaydı",
        "description": "Belirli görev işlemlerinde işlem anı konum kaydı.",
    },
    {
        "code": "photo_proof",
        "name": "Fotoğraflı Kanıt",
        "description": "Görevler için fotoğraf ve dosya kanıtı.",
    },
    {
        "code": "task_templates",
        "name": "Görev Şablonları",
        "description": "Tekrar eden operasyonlar için hazır görev şablonları.",
    },
    {
        "code": "daily_reports",
        "name": "Gün Sonu Raporları",
        "description": "Günlük operasyon özeti ve personel performans raporları.",
    },
    {
        "code": "pdf_export",
        "name": "PDF Rapor Çıktısı",
        "description": "Raporları PDF olarak dışa aktarma.",
    },
    {
        "code": "excel_export",
        "name": "Excel Rapor Çıktısı",
        "description": "Raporları Excel olarak dışa aktarma.",
    },
    {
        "code": "field_tasks",
        "name": "Saha Görevleri",
        "description": "Müşteri, teslimat ve saha lokasyonu odaklı görevler.",
    },
    {
        "code": "setup_wizard",
        "name": "Kurulum Sihirbazı",
        "description": "Müşteri bazlı ilk kurulum akışı.",
    },
    {
        "code": "license_manager",
        "name": "Lisans Yönetimi",
        "description": "Paket, lisans ve kurulum sahipliği takibi.",
    },
    {
        "code": "theme_manager",
        "name": "Tema Yönetimi",
        "description": "Dark mode, light mode ve kullanıcı tema tercihleri.",
    },
]


def get_utc_now() -> datetime:
    """Return current UTC time."""

    return datetime.now(timezone.utc)


def seed_app_settings(db: Session) -> int:
    """Create the initial app settings row if it does not exist."""

    existing = db.query(AppSetting).first()

    if existing is not None:
        return 0

    now = get_utc_now()

    db.add(
        AppSetting(
            app_name="Missio",
            default_timezone="Europe/Istanbul",
            default_theme="dark",
            setup_completed=False,
            created_at=now,
            updated_at=now,
        )
    )

    return 1


def seed_packages(db: Session) -> int:
    """Create or update default package definitions."""

    changed_count = 0
    now = get_utc_now()

    for package_data in PACKAGE_DEFINITIONS:
        code = str(package_data["code"])
        package = db.query(Package).filter(Package.code == code).first()

        if package is None:
            db.add(
                Package(
                    code=code,
                    name=str(package_data["name"]),
                    description=str(package_data["description"]),
                    max_staff_count=int(package_data["max_staff_count"]),
                    is_active=True,
                    created_at=now,
                )
            )
            changed_count += 1
            continue

        package.name = str(package_data["name"])
        package.description = str(package_data["description"])
        package.max_staff_count = int(package_data["max_staff_count"])
        package.is_active = True
        changed_count += 1

    return changed_count


def seed_modules(db: Session) -> int:
    """Create or update default module definitions."""

    changed_count = 0
    now = get_utc_now()

    for module_data in MODULE_DEFINITIONS:
        code = module_data["code"]
        module = db.query(Module).filter(Module.code == code).first()

        if module is None:
            db.add(
                Module(
                    code=code,
                    name=module_data["name"],
                    description=module_data["description"],
                    is_active=True,
                    created_at=now,
                )
            )
            changed_count += 1
            continue

        module.name = module_data["name"]
        module.description = module_data["description"]
        module.is_active = True
        changed_count += 1

    return changed_count


def seed_database(db: Session) -> dict[str, int]:
    """Seed all initial Missio reference data."""

    result = {
        "app_settings": seed_app_settings(db),
        "packages": seed_packages(db),
        "modules": seed_modules(db),
    }

    db.commit()

    return result
