import hashlib
import secrets
from datetime import datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.time import now_utc

# 設計仕様書7.4.1節：パスワードはbcryptでハッシュ化する
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def create_access_token(staff_id: str, role: str) -> tuple[str, int]:
    """アクセストークン発行（sub=担当者ID, role, token_type=access, 有効期限30分）。7.4.1節。"""
    now = now_utc()
    expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    expire = now + expires_delta
    payload = {
        "sub": staff_id,
        "role": role,
        "token_type": "access",
        "iat": now,
        "exp": expire,
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, int(expires_delta.total_seconds())


def create_refresh_token(staff_id: str) -> tuple[str, datetime, datetime]:
    """リフレッシュトークン発行（token_type=refresh、有効期限8時間）。DBの発行記録と対応（D-ISS-08）。"""
    now = now_utc()
    expire = now + timedelta(hours=settings.refresh_token_expire_hours)
    payload = {
        "sub": staff_id,
        "token_type": "refresh",
        "iat": now,
        "exp": expire,
        # jti: DB上のtoken_hash照合に使うランダム値を混入し、同一staff_idの連続ログインでもトークン文字列が一意になるようにする
        "jti": secrets.token_urlsafe(16),
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, now, expire


def hash_token(token: str) -> str:
    """REFRESH_TOKENS.token_hash用。トークン文字列自体は平文でDBに保存しない（7.4.1節、[AI提案]）。"""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def decode_token(token: str) -> dict:
    """署名・有効期限を検証してクレームを返す。無効な場合はJWTErrorを送出する。"""
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


__all__ = [
    "JWTError",
    "hash_password",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "hash_token",
    "decode_token",
]
