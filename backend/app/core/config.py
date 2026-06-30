"""配置管理：从 .env 读取环境变量（Pydantic v2 BaseSettings）。"""

from __future__ import annotations

import logging
import secrets

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """应用配置。从 .env 文件读取，缺失字段用默认值。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 阿里云百炼
    dashscope_api_key: str = ""
    # OpenAI 兼容端点（业务空间专属 key 用专属兼容端点；公网兼容端点作备选）
    dashscope_base_url: str = "https://ws-uimefetm2aof0i9u.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"
    # 模型名（已验证可用，见 test/README.md）
    chat_model: str = "qwen-plus"
    embedding_model: str = "text-embedding-v3"

    # JWT
    jwt_secret_key: str = ""
    jwt_expire_days: int = 7

    # 存储路径
    chroma_db_path: str = "./data/chroma_db"
    meetings_data_path: str = "./data/meetings"
    users_file_path: str = "./data/users.json"

    # 跨域来源：.env 中逗号分隔字符串。
    # 用 str 字段而非 list[str]，避免 pydantic-settings 把它当 JSON 解析；
    # 通过 cors_origins property 拆分为 list。
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    def ensure_jwt_secret(self) -> None:
        """确保 JWT 密钥可用（修正点 #6）。

        未设置时生成临时密钥并打印醒目告警，保证 demo 可直接启动；
        但临时密钥重启后失效，已签发 token 将无法验证。
        应在应用启动时调用一次。
        """
        if not self.jwt_secret_key:
            self.jwt_secret_key = secrets.token_urlsafe(32)
            logger.warning(
                "==========================================================\n"
                "  JWT_SECRET_KEY 未设置！已生成临时密钥，重启后所有已签发\n"
                "  的 token 将失效。请在 .env 中设置长期密钥以持久化会话：\n"
                "    python -c \"import secrets; print(secrets.token_urlsafe(32))\"\n"
                "=========================================================="
            )


# 单例
settings = Settings()
