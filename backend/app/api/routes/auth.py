"""认证路由：注册 / 登录 / 登出。

注册即登录（返回 TokenOut），demo 流程更顺。
登出为无状态空操作 —— JWT 无服务端黑名单，真实登出是前端清 token。
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.core.jwt_handler import create_access_token
from app.schemas.auth import LoginIn, RegisterIn, TokenOut, UserOut
from app.services import user_store

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(body: RegisterIn) -> TokenOut:
    try:
        user = user_store.create_user(body.username, body.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    token = create_access_token({"sub": user["user_id"], "username": user["username"]})
    return TokenOut(access_token=token, user=UserOut(**user_store.public_view(user)))


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn) -> TokenOut:
    user = user_store.get_user_by_username(body.username)
    if user is None or not user_store.verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")

    token = create_access_token({"sub": user["user_id"], "username": user["username"]})
    return TokenOut(access_token=token, user=UserOut(**user_store.public_view(user)))


@router.post("/logout")
def logout() -> dict:
    """无状态登出：JWT 无服务端黑名单，前端清除 token 即完成登出。"""
    return {"message": "已登出"}
