"""FastAPI 应用入口：CORS、lifespan、路由注册、健康检查。"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.api.routes import auth, chat, export, meetings
from app.core.config import settings
from app.services import user_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时确保 JWT 密钥可用 + users.json 存在。"""
    settings.ensure_jwt_secret()      # 修正点 #6：fail-fast/临时密钥
    user_store.ensure_file()
    yield


app = FastAPI(
    title="会议纪要助手",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS：用配置中的来源列表，配合 allow_credentials=True
# （注意：allow_credentials=True 时不能用 ["*"]，必须显式列出来源）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路由注册
app.include_router(auth.router)
app.include_router(meetings.router)
app.include_router(chat.router)
app.include_router(export.router)


@app.get("/api/health", tags=["health"])
def health() -> dict:
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")
