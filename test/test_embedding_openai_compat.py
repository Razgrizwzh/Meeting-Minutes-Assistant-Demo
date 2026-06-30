"""连通性自检：用 OpenAI 兼容模式访问 text-embedding-v3 向量模型。

业务空间专属端点 + 兼容模式。同时打印向量维度，确认与后续 Chroma 存储一致。

运行：cd backend && python ../test/test_embedding_openai_compat.py
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

BACKEND = Path(__file__).resolve().parent.parent / "backend"
load_dotenv(BACKEND / ".env")

API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
BASE_URL = "https://ws-uimefetm2aof0i9u.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"
MODEL = "text-embedding-v3"


def main():
    if not API_KEY:
        print("失败：DASHSCOPE_API_KEY 未设置，请检查 backend/.env")
        sys.exit(1)

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    print(f"请求模型 {MODEL}（OpenAI 兼容模式）...")
    resp = client.embeddings.create(
        model=MODEL,
        input="会议纪要助手向量检索测试",
        # text-embedding-v3 可指定维度，默认 1024；这里显式用 1024 与项目约定一致
        dimensions=1024,
    )
    vec = resp.data[0].embedding
    print(f"向量维度：{len(vec)}")
    print(f"前 5 个分量：{vec[:5]}")
    print("成功：text-embedding-v3 可用（OpenAI 兼容模式）")


if __name__ == "__main__":
    main()