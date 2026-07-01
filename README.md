# 会议纪要助手 · Meeting Minutes Assistant

「会议纪要 + RAG支持的对话追问」助手 demo：粘贴或上传会议转写文本，由 LLM 生成结构化纪要并可导出，再基于向量检索对当前/历史会议做多轮追问，答案流式输出。

> 本仓库为可独立运行的功能演示，定位「本地单机 demo」——认证、存储均为本地实现，不依赖任何云服务（仅 LLM/Embedding 调用阿里云百炼兼容端点）。

---

## 目录

- [功能简介](#功能简介)
- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [环境依赖](#环境依赖)
- [安装与配置](#安装与配置)
- [运行命令](#运行命令)
- [使用指南](#使用指南)
- [常见问题](#常见问题)
- [许可证](#许可证)

---

## 功能简介

- **会议纪要生成**：支持「文本粘贴」与「文件上传（.txt / .docx，自动检测编码）」两种输入；LLM 返回结构化纪要（议题、决策、待办），并以 Markdown 渲染展示。带进度条与预估时长，生成期间不再"卡死无反馈"。
- **RAG 追问（多轮）**：基于 ChromaDB 向量检索对当前/历史会议提问，对话气泡 UI，支持来源标注；AI 回答 **SSE 流式输出**，逐字呈现；回答中的 Markdown（加粗、列表、代码等）自然渲染。
- **对话持久化**：登录用户的追问对话按会议绑定落盘，刷新页面、重开登录、切换历史会议后均可回看。
- **历史管理**：登录用户的历史会议列表，可一键加载、删除（级联清理纪要文件 + 对话记录 + 向量 chunk）。
- **导出**：已保存的纪要可导出为 Markdown（.md）或 Word（.docx），中文文件名正确处理。
- **用户认证**：本地注册/登录，bcrypt 密码哈希 + JWT（7 天有效期），未登录可匿名使用（匿名数据不落库）。
- **深色模式**：浅色/深色双主题一键切换，跟随系统偏好初始化。
- **Tab 布局**：输入区固定高度 + 「会议纪要」/「Chat」Tab 共享大内容区，输入区可收起，贴合「先输入、后看结果、再追问」的使用时序。

---

## 技术栈

### 后端
| 类别 | 选型 |
|------|------|
| Web 框架 | FastAPI + Uvicorn |
| 数据校验 | Pydantic v2 + pydantic-settings |
| 认证 | python-jose(JWT) + bcrypt（密码哈希） |
| 文档解析 | python-docx（读 .docx）、charset-normalizer（.txt 编码检测） |
| LLM | openai SDK（OpenAI 兼容端点调用阿里云百炼 qwen-plus） |
| RAG 框架 | LangChain LCEL —— `create_history_aware_retriever` + `create_stuff_documents_chain`（非已弃用的 `ConversationalRetrievalChain`） |
| Embedding | langchain-openai `OpenAIEmbeddings`（兼容端点 + `text-embedding-v3`，1024 维） |
| 向量库 | ChromaDB（本地持久化，按 user_id / session_id 隔离） |
| 运行时存储 | 本地 JSON 文件（`users.json`、`meetings/{uid}/{mid}.json`） |

### 前端
| 类别 | 选型 |
|------|------|
| 框架 | Vue 3（`<script setup>`） |
| 构建 | Vite 6 |
| 状态管理 | Pinia |
| 路由 | Vue Router 4 |
| UI 组件库 | Element Plus 2（按需自动导入） |
| HTTP | axios（JWT 拦截 + 401 自动登出） |
| Markdown | markdown-it |
| 其他 | uuid（匿名会话 id） |

### LLM / Embedding 服务
- **阿里云百炼**，通过 **OpenAI 兼容端点**调用（业务空间专属 key 仅支持兼容端点，不支持 DashScope 原生 SDK）。
- 纪要生成：`qwen-plus`（OpenAI 兼容 client，一次性生成结构化 JSON）。
- 对话追问：`qwen-plus`（ChatOpenAI，SSE 流式）。
- 向量化：`text-embedding-v3`（1024 维）。

### 平台与语言
- Python ≥ 3.12（3.13 可用，见下方说明）
- Node.js ≥ 18（Vite 6 要求）
- Windows / Linux / macOS 均可运行

---

## 项目结构

```
meeting-assistant/
├── backend/                     后端（FastAPI）
│   ├── app/
│   │   ├── main.py              应用入口：CORS / lifespan / 路由注册
│   │   ├── api/
│   │   │   ├── deps.py          依赖：get_current_user / get_optional_user
│   │   │   └── routes/          auth / meetings / chat / export
│   │   ├── core/                config（pydantic-settings）/ jwt_handler
│   │   ├── services/            document_parser / user_store / meeting_store
│   │   │                        minutes_generator / minutes_renderer
│   │   │                        docx_exporter / rag / session_history / vector_store
│   │   └── schemas/             Pydantic 模型
│   ├── data/                    运行时数据（已 gitignore，仅保留 .gitkeep）
│   │   ├── chroma_db/           向量库持久化
│   │   ├── meetings/{uid}/      会议纪要 + 对话记录（.json / .chat.json）
│   │   └── users.json           用户表（bcrypt hash）
│   ├── requirements.txt
│   ├── .env.example
│   └── .gitignore
├── frontend/                    前端（Vue 3 + Vite）
│   ├── src/
│   │   ├── main.js
│   │   ├── App.vue / views/ / components/ / stores/ / api/ / router/
│   │   └── style.css            全局样式（--ma-* 变量，浅/深色双主题）
│   ├── vite.config.js           /api 代理 + Element Plus 按需自动导入
│   └── package.json
├── meeting_doc/                 （本地测试用会议文本，已 gitignore）
├── plan/                        （开发计划存档，已 gitignore）
├── PROJECT_BRIEF.md             （原始设计简报，已 gitignore）
├── LICENSE
└── README.md
```

---

## 环境依赖

1. **Python**：≥ 3.12（推荐 3.12；3.13 也可，若 Chroma/onnxruntime 装失败则退 3.12）
2. **Node.js**：≥ 18（Vite 6 最低要求），自带 npm
3. **阿里云百炼 API Key**：在 [百炼控制台](https://dashscope.console.aliyun.com/) 创建，选「业务空间专属 key」（兼容端点）或公网 key 均可
4. **Git**（克隆代码用）
5. 操作系统：Windows / Linux / macOS 三端均可

---

## 安装与配置

### 1. 克隆仓库

```bash
git clone https://github.com/Razgrizwzh/Meeting-Minutes-Assistant-Demo.git
cd Meeting-Minutes-Assistant-Demo
```

### 2. 后端配置

```bash
cd backend

# 创建并激活虚拟环境
# Windows (Git Bash / PowerShell)
python -m venv .venv
source .venv/Scripts/activate        # Git Bash
# .venv\Scripts\Activate.ps1         # PowerShell

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate

# 升级 pip 并安装依赖
python -m pip install --upgrade pip
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env                 # Windows Git Bash / Linux / macOS
# copy .env.example .env             # Windows CMD
# 按需编辑 .env，至少填入 DASHSCOPE_API_KEY
```

> **⚠️ `.env` 编码必须是 UTF-8 无 BOM**：Windows 记事本默认可能存成 UTF-8-BOM，会导致首键名带 BOM 读不到 `DASHSCOPE_API_KEY`。用 VS Code 选择「UTF-8（无 BOM）」保存。

`.env` 关键字段：

```ini
DASHSCOPE_API_KEY=                   # 必填：百炼 API Key
DASHSCOPE_BASE_URL=https://.../compatible-mode/v1   # OpenAI 兼容端点
CHAT_MODEL=qwen-plus
EMBEDDING_MODEL=text-embedding-v3

JWT_SECRET_KEY=                      # 留空则启动时自动生成临时密钥（会打印告警，重启后 token 失效）
JWT_EXPIRE_DAYS=7

CHROMA_DB_PATH=./data/chroma_db
MEETINGS_DATA_PATH=./data/meetings
USERS_FILE_PATH=./data/users.json
CORS_ORIGINS=http://localhost:5173
```

> 生成稳定的长期 JWT 密钥：`python -c "import secrets; print(secrets.token_urlsafe(32))"`，把输出填入 `JWT_SECRET_KEY=`。

### 3. 前端配置

```bash
cd ../frontend
npm install
```

---

## 运行命令

需要**同时**启动后端与前端两个进程。

### 后端（终端 1）

```bash
cd backend
source .venv/Scripts/activate        # Windows Git Bash
# .venv\Scripts\Activate.ps1          # Windows PowerShell
# source .venv/bin/activate           # Linux / macOS

uvicorn app.main:app --reload
# 或显式指定：python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

启动后访问 Swagger 文档：`http://localhost:8000/docs`

> **注意**：必须在 `backend/` 目录（含 `app/` 的目录）下运行 `uvicorn`，否则模块路径找不到。Git Bash 激活脚本是 `.venv/Scripts/activate`（非 `bin/activate`）。找不到 `uvicorn` 命令时，用 `python -m uvicorn app.main:app --reload` 绕过 PATH。

### 前端（终端 2）

```bash
cd frontend
npm run dev
```

默认启动在 `http://localhost:5173`。Vite 已配置代理，`/api/*` 请求自动转发到后端 `http://localhost:8000`，开发期同源、无 CORS 障碍。

### 生产构建（可选）

```bash
cd frontend
npm run build        # 产物输出到 frontend/dist/
npm run preview      # 本地预览构建产物（需额外配置后端静态托管或反代）
```

> 三端命令差异主要在虚拟环境激活方式（Windows: `Scripts/activate`，类 Unix: `bin/activate`），其余一致。

---

## 使用指南

1. **启动前后端**后，浏览器打开 `http://localhost:5173`。
2. **注册 / 登录**（右上角）：注册即登录，登录后纪要与对话会持久保存；未登录可匿名使用，但匿名数据不落库、刷新即失。
3. **生成纪要**：在「会议输入」区切换「文本粘贴」/「文件上传」，填写可选的会议名称与日期，点「生成纪要」。生成期间显示进度条，完成后自动切到「会议纪要」Tab 展示。
4. **追问**：切到「Chat」Tab 输入问题，AI 流式回答并标注来源会议；已有的追问记录在切换历史会议或刷新后仍可回看。
5. **历史管理**：左侧栏「历史会议」可点击切换查看，每项右侧 hover 出现删除按钮（二次确认）。
6. **导出**：纪要区右上角「导出」下拉，可选 Markdown 或 Word。
7. **深色模式**：右上角太阳/月亮图标一键切换，自动持久化（localStorage）并跟随系统偏好初始化。
8. **布局折叠**：「会议输入」标题栏右侧收起按钮可把输入区收为一行标题栏，把纵向空间全让给下方纪要/对话区。

---

## 常见问题

**Q：启动后端报 `DASHSCOPE_API_KEY` 读不到？**
A：`.env` 存成了 UTF-8-BOM。用 VS Code 重新存为「UTF-8（无 BOM）」。

**Q：首次打开页面后端 log 出现一条 `401 Unauthorized`（GET /api/meetings/history）？**
A：这是「失效 token 自动清理」机制的预期副产物——localStorage 里残留着上一次会话的过期 token，前端用它请求被拒后会自动清掉，之后不再出现。非 bug，可忽略。

**Q：Python 3.13 安装 chromadb / onnxruntime 失败？**
A：退用 Python 3.12 重建虚拟环境（`py -3.12 -m venv .venv` 或对应系统的 `python3.12`）。

**Q：Vite 启动报端口 5173 被占用？**
A：`Port 5173 is in use, trying another one...` 时检查是否有遗留 dev server 进程（Windows: `netstat -ano | findstr 5173` + `taskkill //PID <pid> //F`；类 Unix: `lsof -ti:5173 | xargs kill`）。若 Vite 自增到非 5173 的端口，需同步修改后端 `.env` 的 `CORS_ORIGINS`。

**Q：生成纪要久久不返回、前端报"生成超时"？**
A：长文本生成耗时较长（qwen-plus 中等长度约 20–40s），前端已放宽到 180s。仍超时可缩短输入文本长度重试。

**Q：对话追问返回 `⚠️ [object Object]`？**
A：通常前后端字段命名不一致所致（已在当前版本修复，前端 camelCase → 后端 snake_case 映射）。若改动过 API，检查 `api/chat.js` 的字段映射。

---

## 安全说明

- `.env`、`.venv/`、运行时数据（`data/` 下除 `.gitkeep` 外）、含 API Key 的 CSV 等均已在 `.gitignore` 中忽略，不会被提交。
- **JWT 存 localStorage** 有 XSS 暴露风险，本地 demo 可接受；生产环境应改用 `HttpOnly` cookie + CSRF 防护。
- 前端 LLM 输出经 `v-html` 渲染 Markdown，**demo 未做 HTML sanitize**；生产环境应加 DOMPurify 等过滤防 XSS。
- 匿名用户共用 `anonymous_pool` 向量集合，按 `session_id` metadata 过滤隔离；登录用户按 `user_id` 独立 collection。

---

## 许可证

见 [LICENSE](LICENSE)。