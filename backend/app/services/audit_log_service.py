from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def get_utc_now() -> datetime:
    """Return current UTC datetime."""

    return datetime.now(timezone.utc)


def serialize_detail(detail: dict[str, Any] | str | None) -> str | None:
    """Serialize audit detail without leaking Python object representation."""

    if detail is None:
        return None

    if isinstance(detail, str):
        return detail

    return json.dumps(
        detail,
        ensure_ascii=False,
        sort_keys=True,
        default=str,
    )


def create_audit_log(
    db: Session,
    *,
    action: str,
    business_id: int | None,
    user_id: int | None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    detail: dict[str, Any] | str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditLog:
    """Create an audit log record and flush it."""

    audit_log = AuditLog(
        business_id=business_id,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        detail=serialize_detail(detail),
        ip_address=ip_address,
        user_agent=user_agent,
        created_at_utc=get_utc_now(),
    )

    db.add(audit_log)
    db.flush()
    db.refresh(audit_log)

    return audit_log
