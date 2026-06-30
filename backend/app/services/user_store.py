"""用户存储：users.json 持久化 + bcrypt 密码哈希（demo 级别）。

users.json 记录 schema：
    {
        "user_id": "uuid4 字符串",
        "username": "alice",
        "password_hash": "$2b$12$...",
        "created_at": "ISO-8601"
    }

匿名用户不落库，用前端生成的 session_id 作为隔离键（见 vector_store.py 的约定）。

密码哈希直接用 ``bcrypt`` 包（hashpw / checkpw），不依赖 passlib ——
passlib 1.7.4 与 bcrypt 4.x 存在 ``__about__`` 属性缺失的兼容噪音，
而 passlib 已停止维护，故直接使用 bcrypt 包更干净。
"""

from __future__ import annotations

import bcrypt
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import settings

_BCRYPT_GENERATIONS = 12

# 内存缓存，启动后首次访问时懒加载
_users_cache: list[dict] | None = None


def _file_path() -> Path:
    return Path(settings.users_file_path)


def _load() -> list[dict]:
    """懒加载 users.json；文件不存在则创建空数组并返回。"""
    global _users_cache
    if _users_cache is not None:
        return _users_cache

    path = _file_path()
    if path.exists():
        _users_cache = json.loads(path.read_text(encoding="utf-8") or "[]")
    else:
        _users_cache = []
        _save(_users_cache)
    return _users_cache


def _save(users: list[dict]) -> None:
    """原子写：先写临时文件再 os.replace，避免 Windows 上写入中断损坏。"""
    global _users_cache
    _users_cache = users
    path = _file_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(users, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def ensure_file() -> None:
    """确保 users.json 存在（应用启动时可调用）。"""
    _load()


def list_users() -> list[dict]:
    return _load()


def get_user_by_username(username: str) -> dict | None:
    for u in _load():
        if u["username"] == username:
            return u
    return None


def get_user_by_id(uid: str) -> dict | None:
    for u in _load():
        if u["user_id"] == uid:
            return u
    return None


def create_user(username: str, password: str) -> dict:
    """创建用户。用户名已存在时抛 ValueError（路由层转 409）。"""
    if get_user_by_username(username) is not None:
        raise ValueError(f"用户名已存在: {username}")

    user = {
        "user_id": str(uuid.uuid4()),
        "username": username,
        "password_hash": _hash_password(password),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    users = _load()
    users.append(user)
    _save(users)
    return user


def _hash_password(plain: str) -> str:
    """bcrypt 哈希，返回 ``$2b$`` 前缀的字符串。"""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(_BCRYPT_GENERATIONS)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """校验明文密码与 bcrypt 哈希是否匹配。"""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        # hashed 不是合法的 bcrypt 哈希格式
        return False


def public_view(user: dict) -> dict:
    """返回不含密码哈希的安全视图。"""
    return {"user_id": user["user_id"], "username": user["username"]}
