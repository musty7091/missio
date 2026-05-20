from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select

import app.models  # noqa: F401
from app.api.dependencies import get_current_user
from app.db.session import SessionLocal, get_db
from app.main import app
from app.models.business import Business
from app.models.task import Task
from app.models.task_event import TaskEvent
from app.models.user import User
from app.repositories.user_repository import normalize_username


BUSINESS_SLUG = "missio-demo-market"
OWNER_USERNAME = "owner"
STAFF_USERNAME = "ahmet"

TASK_TITLE_APPROVE_FLOW = "LIFECYCLE DEMO - Onay akışı"

EXPECTED_EVENT_TYPES = {
    "extra_task_created",
    "task_started",
    "task_completed",
    "task_approved",
}


def get_demo_business(db) -> Business:
    """Return demo business."""

    business = (
        db.execute(select(Business).where(Business.slug == BUSINESS_SLUG))
        .scalars()
        .first()
    )

    if business is None:
        raise RuntimeError(
            "Demo işletme bulunamadı. Önce şu komutu çalıştırın: "
            "python -m app.commands.seed_local_task_demo_data"
        )

    return business


def get_demo_user(
    db,
    *,
    business_id: int,
    username: str,
) -> User:
    """Return demo user."""

    user = (
        db.execute(
            select(User).where(
                User.business_id == business_id,
                User.username == normalize_username(username),
            )
        )
        .scalars()
        .first()
    )

    if user is None:
        raise RuntimeError(
            f"Demo kullanıcı bulunamadı: {username}. "
            "Önce şu komutu çalıştırın: "
            "python -m app.commands.seed_local_task_demo_data"
        )

    return user


def get_lifecycle_approve_task(db, *, business_id: int) -> Task:
    """Return lifecycle approve flow task."""

    task = (
        db.execute(
            select(Task)
            .where(
                Task.business_id == business_id,
                Task.title == TASK_TITLE_APPROVE_FLOW,
                Task.deleted_at_utc.is_(None),
            )
            .order_by(Task.id.desc())
        )
        .scalars()
        .first()
    )

    if task is None:
        raise RuntimeError(
            "Yaşam döngüsü onay akışı görevi bulunamadı. "
            "Önce şu komutu çalıştırın: "
            "python -m app.commands.check_task_lifecycle_flow"
        )

    return task


def count_task_events(db, *, task_id: int) -> int:
    """Return event count for selected task."""

    return len(
        db.execute(
            select(TaskEvent).where(TaskEvent.task_id == task_id)
        )
        .scalars()
        .all()
    )


def build_get_db_override():
    """Build database dependency override."""

    def override_get_db():
        db = SessionLocal()

        try:
            yield db
        finally:
            db.close()

    return override_get_db


def build_get_current_user_override(user: User):
    """Build current user dependency override."""

    def override_get_current_user():
        db = SessionLocal()

        try:
            fresh_user = db.get(User, user.id)

            if fresh_user is None:
                raise RuntimeError("Override kullanıcısı veritabanında bulunamadı.")

            return fresh_user
        finally:
            db.close()

    return override_get_current_user


def assert_event_endpoint_response(
    *,
    response_json: dict,
    expected_task_id: int,
    expected_minimum_count: int,
) -> None:
    """Validate task event endpoint response."""

    total_count = response_json.get("total_count")
    events = response_json.get("events")

    if not isinstance(total_count, int):
        raise RuntimeError("Endpoint cevabında total_count sayısal değil.")

    if not isinstance(events, list):
        raise RuntimeError("Endpoint cevabında events liste değil.")

    if total_count < expected_minimum_count:
        raise RuntimeError(
            "Endpoint beklenen sayıda event döndürmedi. "
            f"Beklenen en az: {expected_minimum_count}, Gelen: {total_count}"
        )

    event_types = set()

    for event in events:
        if event.get("task_id") != expected_task_id:
            raise RuntimeError(
                "Endpoint farklı bir göreve ait event döndürdü. "
                f"Beklenen task_id: {expected_task_id}, Gelen: {event.get('task_id')}"
            )

        event_type = event.get("event_type")

        if isinstance(event_type, str):
            event_types.add(event_type)

    missing_event_types = EXPECTED_EVENT_TYPES - event_types

    if missing_event_types:
        raise RuntimeError(
            "Endpoint beklenen event türlerinin tamamını döndürmedi. "
            f"Eksik event türleri: {sorted(missing_event_types)}"
        )


def check_endpoint_with_user(
    *,
    user: User,
    task: Task,
    expected_minimum_count: int,
    label: str,
) -> None:
    """Check event endpoint with selected user."""

    app.dependency_overrides[get_db] = build_get_db_override()
    app.dependency_overrides[get_current_user] = build_get_current_user_override(user)

    client = TestClient(app)
    response = client.get(f"/api/v1/tasks/{task.id}/events")

    if response.status_code != 200:
        raise RuntimeError(
            f"{label} endpoint kontrolü başarısız. "
            f"HTTP {response.status_code}: {response.text}"
        )

    response_json = response.json()

    assert_event_endpoint_response(
        response_json=response_json,
        expected_task_id=task.id,
        expected_minimum_count=expected_minimum_count,
    )

    print(
        f"[OK] {label} event endpoint kontrolü başarılı. "
        f"task_id={task.id}, total_count={response_json.get('total_count')}"
    )


def main() -> None:
    """Check task event endpoint flow."""

    db = SessionLocal()

    try:
        business = get_demo_business(db)
        owner = get_demo_user(
            db=db,
            business_id=business.id,
            username=OWNER_USERNAME,
        )
        staff = get_demo_user(
            db=db,
            business_id=business.id,
            username=STAFF_USERNAME,
        )
        task = get_lifecycle_approve_task(
            db=db,
            business_id=business.id,
        )

        expected_event_count = count_task_events(db, task_id=task.id)

        if expected_event_count < 4:
            raise RuntimeError(
                "Seçilen görevde yeterli event kaydı yok. "
                "Önce şu komutu tekrar çalıştırın: "
                "python -m app.commands.check_task_lifecycle_flow"
            )

        print("[INFO] Görev event endpoint kontrolü başladı.")
        print(f"[INFO] İşletme: {business.name} | business_id={business.id}")
        print(f"[INFO] Görev: id={task.id} | title={task.title}")
        print(f"[INFO] Veritabanındaki event sayısı: {expected_event_count}")

        check_endpoint_with_user(
            user=owner,
            task=task,
            expected_minimum_count=expected_event_count,
            label="Owner",
        )

        check_endpoint_with_user(
            user=staff,
            task=task,
            expected_minimum_count=expected_event_count,
            label="Atanan personel",
        )

        print("")
        print("[OK] Görev geçmişi endpointi başarılı.")
    finally:
        db.close()
        app.dependency_overrides.clear()


if __name__ == "__main__":
    main()