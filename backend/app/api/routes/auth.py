from datetime import timedelta

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_staff, get_db
from app.core.config import settings
from app.core.errors import BusinessError
from app.core.security import (
    JWTError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_token,
    verify_password,
)
from app.core.time import from_db, now_utc, to_db
from app.models.refresh_token import RefreshToken
from app.models.staff import Staff
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    RefreshRequest,
    RefreshResponse,
)

router = APIRouter(tags=["auth"])


@router.post("/api/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """6.4.1節：担当者ID・パスワードによるログイン認証。"""
    now = now_utc()
    staff = db.get(Staff, payload.staff_id)

    if staff is None:
        raise BusinessError(401, "AUTH_INVALID_CREDENTIALS", "担当者IDまたはパスワードが正しくありません")

    if staff.locked_until is not None and from_db(staff.locked_until) > now:
        raise BusinessError(423, "ACCOUNT_LOCKED", "アカウントがロックされています。しばらくしてから再度お試しください")

    if not verify_password(payload.password, staff.password_hash):
        staff.failed_login_count += 1
        if staff.failed_login_count >= settings.login_max_failed_attempts:
            staff.locked_until = to_db(now + timedelta(minutes=settings.login_lockout_minutes))
        db.commit()
        raise BusinessError(401, "AUTH_INVALID_CREDENTIALS", "担当者IDまたはパスワードが正しくありません")

    staff.failed_login_count = 0
    staff.locked_until = None

    access_token, expires_in = create_access_token(staff.staff_id, staff.role)
    refresh_token, issued_at, expires_at = create_refresh_token(staff.staff_id)

    db.add(
        RefreshToken(
            staff_id=staff.staff_id,
            token_hash=hash_token(refresh_token),
            issued_at=to_db(issued_at),
            expires_at=to_db(expires_at),
        )
    )
    db.commit()

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
        staff_id=staff.staff_id,
        staff_name=staff.name,
    )


@router.post("/api/auth/refresh", response_model=RefreshResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    """6.4.2節：リフレッシュトークンによるアクセストークン再発行。"""
    try:
        claims = decode_token(payload.refresh_token)
    except JWTError:
        raise BusinessError(401, "REFRESH_TOKEN_INVALID", "リフレッシュトークンが無効または期限切れです")

    if claims.get("token_type") != "refresh":
        raise BusinessError(401, "REFRESH_TOKEN_INVALID", "リフレッシュトークンが無効です")

    token_hash = hash_token(payload.refresh_token)
    record = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    now = now_utc()
    if (
        record is None
        or record.revoked_at is not None
        or from_db(record.expires_at) <= now
    ):
        raise BusinessError(401, "REFRESH_TOKEN_INVALID", "リフレッシュトークンが無効または期限切れです")

    staff = db.get(Staff, record.staff_id)
    if staff is None:
        raise BusinessError(401, "REFRESH_TOKEN_INVALID", "リフレッシュトークンが無効です")

    access_token, expires_in = create_access_token(staff.staff_id, staff.role)
    return RefreshResponse(access_token=access_token, expires_in=expires_in)


@router.post("/api/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    payload: LogoutRequest,
    db: Session = Depends(get_db),
    current_staff=Depends(get_current_staff),
):
    """6.4.3節：リフレッシュトークンの失効（ISS-010、D-ISS-08）。"""
    token_hash = hash_token(payload.refresh_token)
    record = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    if record is not None and record.revoked_at is None:
        record.revoked_at = to_db(now_utc())
        db.commit()
    return None
