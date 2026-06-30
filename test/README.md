# 连通性自检测试

用真实 API Key 验证能否访问百炼模型。运行前需在 `backend/.env` 设置 `DASHSCOPE_API_KEY`。

所有测试都从 `backend/.env` 读取密钥，请在 `backend/` 目录下运行（已装好 venv 依赖）：

```bash
cd backend
source .venv/Scripts/activate
python ../test/test_chat_openai_compat.py        # qwen3.7-plus 对话（兼容模式）
python ../test/test_embedding_openai_compat.py   # text-embedding-v3 向量（兼容模式）
python ../test/test_chat_dashscope_native.py     # 原生 SDK（预期失败，见下）
```

## 测试结论（2026-06-29 实测）

当前 API Key 为**业务空间专属 key**（`sk-ws-` 前缀，工作空间 `ws-uimefetm2aof0i9u`）。

| 端点 | 模式 | 结果 |
|------|------|------|
| 业务空间专属兼容端点 `…/compatible-mode/v1` | OpenAI 兼容 | ✅ qwen3.7-plus / text-embedding-v3 均可用 |
| 公网 `dashscope.aliyuncs.com/compatible-mode/v1` | OpenAI 兼容 | ✅ 可用 |
| 业务空间专属原生端点 `…/api/v1` | DashScope 原生 SDK | ❌ url error |
| 公网 `dashscope.aliyuncs.com/api/v1` | DashScope 原生 SDK | ❌ 400 InvalidParameter |

**核心结论：该 key 只能用 OpenAI 兼容模式，不能用 DashScope 原生 SDK 模式。**

`text-embedding-v3` 实测向量维度 1024（与项目约定一致）。

## 对项目架构的影响

原计划 RAG 链路用 `langchain-community` 的 `ChatTongyi` / `DashScopeEmbeddings`，
但这两个类内部用的是 **DashScope 原生 SDK**，在业务空间 key 下会走不通。

**调整方案（下一轮开发时落实）：** RAG 链改为基于 `langchain-openai` 的
`ChatOpenAI` / `OpenAIEmbeddings`，把 `base_url` 指向百炼兼容端点、`model` 设为
`qwen3.7-plus` / `text-embedding-v3`。这样：

- 纪要生成、向量化、RAG 对话**统一走 OpenAI 兼容模式**，与已验证可用的路径一致；
- 仍可复用 LangChain 的 LCEL（`create_history_aware_retriever` 等修正点 #1 方案）；
- 需在 `requirements.txt` 加 `langchain-openai`，移除 `langchain-community` 的 Tongyi 依赖。

端点选择：优先用业务空间专属兼容端点（与 key 绑定的工作空间一致），
公网兼容端点作为备选。