from dataclasses import dataclass

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.errors import BusinessError
from app.core.security import JWTError, decode_token
from app.db.session import get_db

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass
class CurrentStaff:
    staff_id: str
    role: str


def _decode_current_staff(credentials: HTTPAuthorizationCredentials | None) -> CurrentStaff | None:
    """Authorizationヘッダーの検証本体。無効・未提供の場合はNoneを返す（例外送出はしない）。"""
    if credentials is None:
        return None
    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        return None

    if payload.get("token_type") != "access":
        return None

    staff_id = payload.get("sub")
    role = payload.get("role")
    if not staff_id or not role:
        return None

    return CurrentStaff(staff_id=staff_id, role=role)


def get_current_staff(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> CurrentStaff:
    """Authorization: Bearer <access_token> を検証する（設計仕様書7.4.1節）。無効・未提供は401。"""
    current = _decode_current_staff(credentials)
    if current is None:
        raise BusinessError(401, "AUTH_TOKEN_INVALID", "認証が必要です")
    return current


def get_current_staff_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> CurrentStaff | None:
    """認証を必須としない版。無効・未提供の場合はNoneを返す（POST /api/staffのブートストラップ用途）。"""
    return _decode_current_staff(credentials)


def require_admin(current_staff: CurrentStaff = Depends(get_current_staff)) -> CurrentStaff:
    """F-10（値引き・税率管理機能）向けの管理者ロール検証（AuthService.requireAdminRole()、5.3節/7.4.1節）。"""
    if current_staff.role != "admin":
        raise BusinessError(403, "ADMIN_ROLE_REQUIRED", "この操作には管理者権限が必要です")
    return current_staff


__all__ = [
    "get_db",
    "get_current_staff",
    "get_current_staff_optional",
    "require_admin",
    "CurrentStaff",
]
