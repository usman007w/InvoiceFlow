from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import COOKIE_NAME
from app.core.security import decode_token
from app.db import User, get_db


def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get(COOKIE_NAME)
    user_id = decode_token(token) if token else None
    user = db.get(User, user_id) if user_id else None
    if user is None or not user.is_active:
        raise HTTPException(401, "Not authenticated")
    return user


def require_roles(*roles):
    def checker(user: User = Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(403, "Not allowed")
        return user

    return checker