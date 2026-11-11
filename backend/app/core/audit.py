import json

from app.db import AuditLog


def log_event(db, action, user=None, email=None, target=None, detail=None, request=None):
    entry = AuditLog(
        action=action,
        user_id=user.id if user else None,
        company_id=user.company_id if user else None,
        email=user.email if user else email,
        target=target,
        detail=json.dumps(detail) if detail is not None else None,
        ip=request.client.host if request is not None and request.client else None,
    )
    db.add(entry)
    db.commit()