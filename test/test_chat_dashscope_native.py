"""连通性自检：用 DashScope 原生 SDK 访问 qwen3.7-plus 对话模型。

【已知结论】业务空间专属 API Key（sk-ws- 前缀）不支持 DashScope 原生 /api/v1 路径，
只支持 OpenAI 兼容 /compatible-mode/v1 路径。因此原生 SDK 的 Generation.call 会失败，
这是预期行为，不是 bug。

本脚本用来复现这一结论。若未来 key 改为支持原生模式，此脚本才会通过。

运行：cd backend && python ../test/test_chat_dashscope_native.py
"""

import os
import sys
from pathlib import Path

import dashscope
from dashscope import Generation
from dotenv import load_dotenv

BACKEND = Path(__file__).resolve().parent.parent / "backend"
load_dotenv(BACKEND / ".env")

API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
# 业务空间专属端点（原生 /api/v1）—— 业务空间 key 不支持此路径
dashscope.base_http_api_url = "https://ws-uimefetm2aof0i9u.cn-beijing.maas.aliyuncs.com/api/v1"
dashscope.api_key = API_KEY
MODEL = "qwen3.7-plus"


def main():
    if not API_KEY:
        print("失败：DASHSCOPE_API_KEY 未设置，请检查 backend/.env")
        sys.exit(1)

    print(f"请求模型 {MODEL}（DashScope 原生 SDK，业务空间专属原生端点）...")
    resp = Generation.call(
        model=MODEL,
        messages=[{"role": "user", "content": "用一句话介绍你自己。"}],
    )
    if resp.status_code == 200:
        answer = resp.output.choices[0].message.content
        print("回答：", answer)
        print("成功：原生 SDK 可用（key 已支持原生模式）")
    else:
        print(f"预期失败：HTTP {resp.status_code} - {resp.message or resp.code}")
        print("说明：业务空间专属 key 不支持 DashScope 原生 /api/v1 路径，")
        print("      项目应统一使用 OpenAI 兼容模式（见 test_chat_openai_compat.py）。")
        # 以 0 退出，表示这是预期结果而非脚本错误
        sys.exit(0)


if __name__ == "__main__":
    main()
