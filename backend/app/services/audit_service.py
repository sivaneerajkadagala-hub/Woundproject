"""
Audit logging service.

Provides a single `log_action` helper that persists an AuditLog record.
This is the canonical audit logging mechanism for the application — do not
create a parallel audit system.
"""
import json
import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.models.audit import AuditLog

logger = logging.getLogger("wound_ai.audit")


def log_action(
    db: Session,
    user_id: Optional[int],
    action: str,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    details: Optional[str] = None,
) -> AuditLog:
    """
    Persist an audit log entry.

    Args:
        db: SQLAlchemy session.
        user_id: ID of the user performing the action (None for system events).
        action: Short action name (e.g. "login", "patient_create").
        target_type: Resource type (e.g. "Patient", "WoundCase").
        target_id: Resource ID (string for flexibility).
        details: Human-readable or JSON-serialized extra context.
                 Do NOT put passwords, tokens, or secrets here.

    Returns:
        The created AuditLog record.
    """
    entry = AuditLog(
        user_id=user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    logger.info(f"AUDIT user={user_id} action={action} target={target_type}:{target_id}")
    return entry
