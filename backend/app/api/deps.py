"""共享依赖：OAuth2 scheme + get_current_user。"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.jwt_handler import decode_token
from app.services import user_store

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
# 用于"登录可选"端点（如 /meetings/generate）：无 token/无效 token 不抛 401，返回 None
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """从 JWT 解析当前登录用户。无效/过期 token 抛 401。"""
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或已过期的凭证",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="凭证缺少用户标识")

    user = user_store.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
    return user


async def get_optional_user(token: str | None = Depends(oauth2_scheme_optional)) -> dict | None:
    """登录可选：有效 token 返回用户，无 token/无效 token 返回 None（不抛 401）。

    供 /meetings/generate 这类"匿名也能用、登录则保存历史"的端点。
    """
    if not token:
        return None
    payload = decode_token(token)
    if payload is None:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    return user_store.get_user_by_id(user_id)
