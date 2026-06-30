"""连通性自检：用 OpenAI 兼容模式访问 qwen3.7-plus 对话模型。

业务空间专属 API Key（sk-ws- 前缀）需用专属端点，而非公网 dashscope 端点。
端点来自「默认业务空间-apiKey-5905219.csv」中的 openAiCompatible 字段。

运行：cd backend && python ../test/test_chat_openai_compat.py
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

# 从 backend/.env 加载 DASHSCOPE_API_KEY
BACKEND = Path(__file__).resolve().parent.parent / "backend"
load_dotenv(BACKEND / ".env")

API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
# 业务空间专属 OpenAI 兼容端点
BASE_URL = "https://ws-uimefetm2aof0i9u.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"
MODEL = "qwen3.7-plus"


def main():
    if not API_KEY:
        print("失败：DASHSCOPE_API_KEY 未设置，请检查 backend/.env")
        sys.exit(1)

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    print(f"请求模型 {MODEL}（OpenAI 兼容模式）...")
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": "用一句话介绍你自己。"}],
    )
    answer = resp.choices[0].message.content
    print("回答：", answer)
    print("成功：qwen3.7-plus 可用（OpenAI 兼容模式）")


if __name__ == "__main__":
    main()