from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.audit import log_event
from app.core.config import (
    COOKIE_NAME,
    COOKIE_SECURE,
    LOCKOUT_MINUTES,
    MAX_FAILED_LOGINS,
    TOKEN_MINUTES,
)
from app.core.security import burn_time, create_token, hash_password, verify_password
from app.db import AuditLog, User, get_db, utcnow

router = APIRouter(tags=["auth"])

EMAIL = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class LoginBody(BaseModel):
    email: str = Field(pattern=EMAIL, max_length=254)
    password: str = Field(min_length=1, max_length=200)


class NewUser(BaseModel):
    email: str = Field(pattern=EMAIL, max_length=254)
    password: str = Field(min_length=12, max_length=200)
    role: str = Field(pattern="^(admin|reviewer|viewer)$")


def user_info(user):
    return {"id": user.id, "email": user.email, "role": user.role, "company_id": user.company_id}


@router.post("/auth/login")
def login(body: LoginBody, request: Request, response: Response, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        burn_time(body.password)
        log_event(db, "login_failed", email=email, request=request)
        raise HTTPException(401, "Invalid email or password")
    if user.locked_until and user.locked_until > utcnow():
        log_event(db, "login_blocked", user=user, request=request)
        raise HTTPException(429, "Too many failed attempts. Try again later.")
    if not user.is_active or not verify_password(body.password, user.password_hash):
        user.failed_logins += 1
        if user.failed_logins >= MAX_FAILED_LOGINS:
            user.locked_until = utcnow() + timedelta(minutes=LOCKOUT_MINUTES)
            user.failed_logins = 0
        db.commit()
        log_event(db, "login_failed", user=user, request=request)
        raise HTTPException(401, "Invalid email or password")
    user.failed_logins = 0
    user.locked_until = None
    db.commit()
    response.set_cookie(
        COOKIE_NAME,
        create_token(user.id),
        max_age=TOKEN_MINUTES * 60,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="strict",
        path="/",
    )
    log_event(db, "login", user=user, request=request)
    return user_info(user)


@router.post("/auth/logout")
def logout(
    request: Request,
    response: Response,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    response.delete_cookie(COOKIE_NAME, path="/")
    log_event(db, "logout", user=user, request=request)
    return {"status": "logged_out"}


@router.get("/auth/me")
def me(user: User = Depends(get_current_user)):
    return user_info(user)


@router.post("/users", status_code=201)
def create_user(
    body: NewUser,
    request: Request,
    admin: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    email = body.email.strip().lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "User already exists")
    user = User(
        email=email,
        password_hash=hash_password(body.password),
        role=body.role,
        company_id=admin.company_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    log_event(
        db, "user_created", user=admin, target=f"user:{user.id}",
        detail={"role": user.role}, request=request,
    )
    return user_info(user)


@router.get("/audit")
def list_audit(
    limit: int = 100,
    admin: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    limit = max(1, min(limit, 500))
    rows = db.scalars(
        select(AuditLog)
        .where(AuditLog.company_id == admin.company_id)
        .order_by(AuditLog.id.desc())
        .limit(limit)
    )
    return [
        {
            "id": r.id,
            "time": r.created_at.isoformat(),
            "action": r.action,
            "email": r.email,
            "target": r.target,
            "detail": r.detail,
            "ip": r.ip,
        }
        for r in rows
    ]