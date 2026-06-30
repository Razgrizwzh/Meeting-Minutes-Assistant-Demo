# 会议纪要助手 —— 后端

基于 FastAPI 的会议纪要生成与 RAG 追问后端。

## 快速开始（Windows / Git Bash）

```bash
cd c:/Users/cxksx/Desktop/meeting-assistant/backend

# 1. 创建并激活虚拟环境
python -m venv .venv
source .venv/Scripts/activate          # Git Bash 激活路径（非 bin/activate）
python -m pip install --upgrade pip

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env                   # 然后编辑 .env，填入 DASHSCOPE_API_KEY
                                        # JWT_SECRET_KEY 可不填（会生成临时密钥），但建议填

# 4. 启动
uvicorn app.main:app --reload
```

启动后：

- API 文档（Swagger）：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

## 注意事项

- **`.env` 编码**：保存为 UTF-8 **无 BOM**，否则首个键名会带 BOM 字符导致读取失败（症状：密钥看似未设）。
- **Python 3.13 与 Chroma**：若 `pip install` 在 chromadb/onnxruntime 上失败，可改用 3.12 建环境：`py -3.12 -m venv .venv`。本轮不导入 Chroma，装失败不影响脚手架验收。
- **端口**：后端默认 8000，前端 Vite 默认 5173。若 5173 被占用导致 Vite 自增端口，需同步修改 `.env` 的 `CORS_ORIGINS`。

## 当前实现状态（脚手架轮）

- 完整：认证（注册/登录/登出）、文档解析（.txt 编码检测 + .docx 读取）、配置管理、JWT 工具
- 占位（后续轮实现）：纪要生成、RAG 追问、向量化、导出、历史会议管理
