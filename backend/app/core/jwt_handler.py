"""JWT 工具：签发与解码 token（python-jose，HS256，7 天有效期）。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.core.config import settings

ALGORITHM = "HS256"


def create_access_token(data: dict, expires_days: int | None = None) -> str:
    """签发 JWT。data 通常含 ``sub``（user_id）等自定义声明。"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        days=expires_days if expires_days is not None else settings.jwt_expire_days
    )
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=ALGORITHM)


def decode_token(token: str) -> dict | None:
    """解码并验证 JWT。无效或过期返回 None。"""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
