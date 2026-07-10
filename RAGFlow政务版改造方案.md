# GovRAG —— 政务版智能知识库系统技术方案

## 一、项目概述

### 1.1 背景与目标

参照 [RAGFlow](https://github.com/infiniflow/ragflow) 核心设计理念与交互范式，从零新建前后端分离架构，完整复刻其三层鉴权体系、文档处理流水线、LCEL-RAG 检索增强生成逻辑，同时剔除 Agent 编排、MCP 协议、外部连接器、记忆模块、代码沙箱等非政务场景模块，仅保留四大核心骨架，打造适配政府机关单位的内网知识库问答系统。
原项目本地地址：D:\9_Project\VsStudioProject\ragflow-main

### 1.2 技术选型

| 层级 | 技术 | 版本 | 说明 |
|------|------|------|------|
| **前端框架** | Next.js | 14（App Router） | SSR/SSG，对齐 RAGFlow 原生 React 生态 |
| **前端语言** | TypeScript | 5.x | 严格模式 |
| **前端样式** | TailwindCSS | 3.x | 原子化 CSS，政务系统适配性好 |
| **后端框架** | Flask | 3.x | Blueprint 分层路由，对齐原项目 |
| **ORM** | SQLAlchemy | 2.x | 替代 Peewee，扩展性更强 |
| **任务队列** | Celery | 5.x | Redis Broker，批量文档处理 |
| **缓存** | Redis | 7.x | 会话、缓存、消息队列 |
| **关系数据库** | MYSQL | 8.0 | 主数据存储 |
| **向量数据库** | Infinity | latest | 高性能向量检索，对齐 RAGFlow |
| **对象存储** | MinIO | latest | S3 兼容，文件存储 |
| **部署方式** | 本地直接运行 | — | Flask + Celery + Next.js 均在宿主机启动，无需容器化 |

### 1.3 与 RAGFlow 的对照关系

| RAGFlow 原模块 | GovRAG 对应实现 | 策略 |
|---------------|-----------------|------|
| `api/ragflow_server.py` | `backend/app.py`（Flask 工厂模式） | 复刻 |
| `api/apps/auth/` | `backend/api/auth/` | 复刻+增强 |
| `api/db/db_models.py`（Peewee） | `backend/models/`（SQLAlchemy） | 重写 |
| `rag/`（RAG 核心） | `backend/rag/` | 复刻 |
| `deepdoc/`（文档解析） | `backend/deepdoc/` | 复刻 |
| `agent/` | **删除** | — |
| `mcp/` | **删除** | — |
| `memory/` | **删除** | — |
| `web/`（React + Vite） | `frontend/`（Next.js 14） | 重写 |
| `conf/llm_factories.json` | `backend/config/llm_factories.json` | 复用+扩展 |

---

## 二、项目目录结构

```
Office_RagFlow/
├── .env                                  # 环境变量（本地配置）
├── .env.example                          # 环境变量模板
├── README.md
│
├── frontend/                             # Next.js 14 前端
│   ├── next.config.js
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── package.json
│   ├── src/
│   │   ├── app/                          # App Router 页面
│   │   │   ├── layout.tsx                # 根布局（三栏骨架）
│   │   │   ├── page.tsx                  # 首页仪表盘
│   │   │   ├── (auth)/                   # 认证路由组
│   │   │   │   ├── login/
│   │   │   │   │   └── page.tsx          # 登录页
│   │   │   │   └── sso-callback/
│   │   │   │       └── page.tsx          # SSO 回调
│   │   │   ├── (main)/                   # 主业务路由组（需登录）
│   │   │   │   ├── layout.tsx            # 主布局（侧边栏+内容）
│   │   │   │   ├── datasets/
│   │   │   │   │   ├── page.tsx          # 数据集列表
│   │   │   │   │   └── [id]/
│   │   │   │   │       ├── page.tsx      # 数据集详情（概览）
│   │   │   │   │       ├── documents/    # 文档管理
│   │   │   │   │       ├── chunks/       # 切片管理
│   │   │   │   │       ├── testing/      # 检索测试
│   │   │   │   │       └── settings/     # 配置
│   │   │   │   ├── chats/
│   │   │   │   │   ├── page.tsx          # 对话列表
│   │   │   │   │   └── [id]/
│   │   │   │   │       └── page.tsx      # 对话详情
│   │   │   │   ├── searches/
│   │   │   │   │   ├── page.tsx          # 检索列表
│   │   │   │   │   └── [id]/
│   │   │   │   │       └── page.tsx      # 检索详情
│   │   │   │   ├── files/
│   │   │   │   │   └── page.tsx          # 文件管理
│   │   │   │   └── models/
│   │   │   │       └── page.tsx          # 模型配置
│   │   │   ├── (admin)/                  # 管理员路由组
│   │   │   │   ├── layout.tsx
│   │   │   │   ├── users/
│   │   │   │   │   └── page.tsx          # 用户管理
│   │   │   │   ├── roles/
│   │   │   │   │   └── page.tsx          # 角色管理
│   │   │   │   ├── departments/
│   │   │   │   │   └── page.tsx          # 部门管理
│   │   │   │   ├── audit/
│   │   │   │   │   └── page.tsx          # 审计日志
│   │   │   │   ├── monitoring/
│   │   │   │   │   └── page.tsx          # 系统监控
│   │   │   │   └── settings/
│   │   │   │       └── page.tsx          # 系统设置
│   │   │   └── api/                      # Next.js API Routes（BFF层）
│   │   │       └── proxy/[...path]/
│   │   │           └── route.ts          # 后端请求代理
│   │   ├── components/                   # 业务组件
│   │   │   ├── layout/
│   │   │   │   ├── Sidebar.tsx           # 侧边导航
│   │   │   │   ├── Header.tsx            # 顶部栏
│   │   │   │   └── ThreeColumnLayout.tsx # 三栏布局容器
│   │   │   ├── dataset/
│   │   │   │   ├── DatasetCard.tsx       # 数据集卡片
│   │   │   │   ├── DatasetUpload.tsx     # 文件上传（拖拽+进度）
│   │   │   │   ├── DocumentList.tsx      # 文档列表（虚拟滚动）
│   │   │   │   ├── ChunkViewer.tsx       # 切片预览
│   │   │   │   ├── TagSelector.tsx       # 公文标签选择器
│   │   │   │   └── SecurityLevelPicker.tsx # 涉密等级选择器
│   │   │   ├── chat/
│   │   │   │   ├── ChatWindow.tsx        # 对话窗口
│   │   │   │   ├── MessageBubble.tsx     # 消息气泡
│   │   │   │   ├── CitationCard.tsx      # 溯源引用卡片
│   │   │   │   └── FeedbackButtons.tsx   # 满意度反馈
│   │   │   ├── search/
│   │   │   │   ├── SearchBar.tsx         # 检索输入
│   │   │   │   ├── SearchResult.tsx      # 检索结果
│   │   │   │   └── HighlightText.tsx     # 高亮标注文本
│   │   │   ├── admin/
│   │   │   │   ├── AuditTable.tsx        # 审计日志表格
│   │   │   │   ├── UserForm.tsx          # 用户表单
│   │   │   │   └── DeptTree.tsx          # 部门树形组件
│   │   │   └── common/
│   │   │       ├── MarkdownRenderer.tsx  # Markdown 渲染（含引用锚点）
│   │   │       ├── FileUploader.tsx      # 通用文件上传器
│   │   │       └── WatermarkOverlay.tsx  # 水印遮罩层
│   │   ├── hooks/                        # 自定义 Hooks
│   │   │   ├── useAuth.ts               # 鉴权 Hook
│   │   │   ├── useChat.ts               # 对话 SSE 流式 Hook
│   │   │   ├── useDataset.ts            # 数据集操作 Hook
│   │   │   └── useAudit.ts              # 审计埋点 Hook
│   │   ├── lib/                          # 工具库
│   │   │   ├── api-client.ts            # Axios 封装（JWT+审计埋点）
│   │   │   ├── auth-utils.ts            # Token 管理
│   │   │   └── security-level.ts        # 涉密等级工具函数
│   │   ├── stores/                       # 状态管理（Zustand）
│   │   │   ├── auth-store.ts            # 认证状态
│   │   │   ├── chat-store.ts            # 对话状态
│   │   │   └── ui-store.ts              # UI 状态（侧边栏、主题）
│   │   └── types/                        # TypeScript 类型定义
│   │       ├── auth.ts
│   │       ├── dataset.ts
│   │       ├── chat.ts
│   │       ├── document.ts
│   │       └── admin.ts
│
├── backend/                              # Flask 后端
│   ├── app.py                            # Flask 应用工厂入口
│   ├── config.py                         # 配置管理
│   ├── celery_app.py                     # Celery 实例
│   ├── tasks/                            # Celery 异步任务
│   │   ├── __init__.py
│   │   ├── document_tasks.py             # 文档解析+向量化任务
│   │   └── maintenance_tasks.py          # 定期清理任务
│   ├── api/                              # API 路由层（Flask Blueprint）
│   │   ├── __init__.py                   # Blueprint 注册中心
│   │   ├── auth/
│   │   │   ├── __init__.py               # auth_bp
│   │   │   ├── login.py                  # 登录、SSO 回调
│   │   │   └── middleware.py             # JWT 鉴权装饰器
│   │   ├── v1/                           # /api/v1/*
│   │   │   ├── __init__.py
│   │   │   ├── dataset.py               # 数据集 CRUD
│   │   │   ├── document.py              # 文档上传/管理
│   │   │   ├── chunk.py                 # 切片管理
│   │   │   ├── chat.py                  # 对话/问答
│   │   │   ├── search.py               # 检索
│   │   │   ├── file.py                  # 文件管理
│   │   │   ├── model.py                 # 模型配置
│   │   │   ├── user.py                  # 用户信息
│   │   │   └── tenant.py               # 租户管理
│   │   └── admin/                        # /api/v1/admin/*
│   │       ├── __init__.py
│   │       ├── users.py                  # 用户管理
│   │       ├── roles.py                  # 角色权限
│   │       ├── departments.py            # 部门管理
│   │       ├── audit.py                  # 审计日志
│   │       ├── monitoring.py             # 系统监控
│   │       ├── stats.py                  # 使用统计
│   │       └── system.py                 # 系统配置
│   ├── services/                         # 业务服务层
│   │   ├── __init__.py
│   │   ├── auth_service.py               # 认证+租户服务
│   │   ├── dataset_service.py            # 数据集服务
│   │   ├── document_service.py           # 文档解析+切块服务
│   │   ├── chat_service.py               # RAG 问答服务
│   │   ├── search_service.py             # 检索服务
│   │   ├── model_service.py              # 模型配置服务
│   │   ├── file_service.py               # 文件存储服务
│   │   └── audit_service.py              # 审计日志服务
│   ├── rag/                              # RAG 核心引擎（复刻 RAGFlow rag/）
│   │   ├── __init__.py
│   │   ├── retrieval/                    # 检索模块
│   │   │   ├── __init__.py
│   │   │   ├── vector_search.py          # 向量检索（Infinity）
│   │   │   ├── keyword_search.py         # 关键词检索（BM25）
│   │   │   ├── hybrid_search.py          # 混合检索+RRF 融合
│   │   │   └── reranker.py               # 重排序（BGE-Reranker）
│   │   ├── generation/                   # 生成模块
│   │   │   ├── __init__.py
│   │   │   ├── prompt_builder.py         # Prompt 模板构建
│   │   │   ├── context_assembler.py      # 上下文拼接（溯源引用）
│   │   │   └── llm_client.py             # LLM 调用客户端
│   │   ├── pipeline/                     # LCEL 流水线
│   │   │   ├── __init__.py
│   │   │   ├── rag_pipeline.py           # RAG 主流水线
│   │   │   └── steps.py                  # 流水线步骤定义
│   │   ├── nlp/                          # NLP 工具
│   │   │   ├── __init__.py
│   │   │   ├── tokenizer.py              # 分词器
│   │   │   └── text_cleaner.py           # 文本清洗
│   │   └── prompts/                      # Prompt 模板（JSON）
│   │       ├── qa_prompt.json
│   │       ├── summary_prompt.json
│   │       └── system_prompt.json
│   ├── deepdoc/                          # 文档解析引擎（复刻 RAGFlow deepdoc/）
│   │   ├── __init__.py
│   │   ├── parser/
│   │   │   ├── __init__.py
│   │   │   ├── pdf_parser.py             # PDF 解析
│   │   │   ├── word_parser.py            # Word 解析
│   │   │   ├── excel_parser.py           # Excel 解析
│   │   │   ├── image_parser.py           # 图片 OCR 解析
│   │   │   ├── ofd_parser.py             # OFD 版式文档解析
│   │   │   ├── wps_parser.py             # WPS 格式解析
│   │   │   └── markdown_parser.py        # Markdown 解析
│   │   ├── chunker/                      # 切块模块
│   │   │   ├── __init__.py
│   │   │   ├── naive_chunker.py          # 固定大小切块
│   │   │   ├── semantic_chunker.py       # 语义切块
│   │   │   └── document_chunker.py       # 公文结构化切块
│   │   ├── ocr/                          # OCR 模块
│   │   │   ├── __init__.py
│   │   │   ├── paddleocr_engine.py       # PaddleOCR
│   │   │   └── tesseract_engine.py       # Tesseract
│   │   └── table/                        # 表格提取
│   │       ├── __init__.py
│   │       └── table_extractor.py
│   ├── models/                           # SQLAlchemy 数据模型
│   │   ├── __init__.py
│   │   ├── base.py                       # Base Model
│   │   ├── tenant.py                     # 租户
│   │   ├── user.py                       # 用户
│   │   ├── role.py                       # 角色
│   │   ├── department.py                 # 部门
│   │   ├── dataset.py                    # 数据集
│   │   ├── document.py                   # 文档
│   │   ├── chunk.py                      # 切片
│   │   ├── chat.py                       # 对话
│   │   ├── chat_message.py              # 聊天消息
│   │   ├── file.py                       # 文件
│   │   ├── tag.py                        # 标签
│   │   ├── model_config.py              # 模型配置
│   │   ├── audit_log.py                 # 审计日志
│   │   └── qa_record.py                 # 问答记录
│   ├── migrations/                       # Alembic 数据库迁移
│   │   ├── alembic.ini
│   │   ├── env.py
│   │   └── versions/
│   ├── middleware/                        # 中间件
│   │   ├── __init__.py
│   │   ├── auth_middleware.py            # JWT + API Key 鉴权
│   │   ├── audit_middleware.py           # 操作审计埋点
│   │   ├── rate_limit_middleware.py      # 频率限制
│   │   └── security_level_middleware.py  # 涉密等级拦截
│   ├── utils/                            # 工具
│   │   ├── __init__.py
│   │   ├── jwt_utils.py                  # JWT 生成/校验
│   │   ├── crypto_utils.py               # 加密工具
│   │   ├── s3_client.py                  # MinIO S3 客户端
│   │   ├── infinity_client.py            # Infinity 向量库客户端
│   │   └── response.py                   # 统一响应格式
│   └── config/                           # 配置文件
│       ├── llm_factories.json            # LLM 厂商配置
│       ├── all_models.json               # 模型目录
│       └── system_settings.json          # 系统设置
│
└── scripts/                              # 运维脚本
    ├── init.sql                          # 数据库初始化（直接在 MySQL 中执行）
    ├── init_db.py                        # 数据库初始化 Python 脚本
    ├── seed_data.py                      # 初始化种子数据
    ├── start_backend.bat                 # 后端启动脚本（Windows）
    ├── start_worker.bat                  # Celery Worker 启动脚本（Windows）
    └── start_frontend.bat                # 前端启动脚本（Windows）
```

---

### 2.1 命名规范

本项目遵循统一的命名规范，各技术栈在核心原则对齐的基础上适配各自语言惯例。

#### 2.1.1 核心原则

| 原则 | 说明 |
|------|------|
| **一致性优先** | 同一技术栈内的命名风格必须统一，禁止混用 |
| **语义明确** | 命名应直接表达意图，避免缩写歧义（`department` 优于 `dept` 除非上下文明确） |
| **约定优于配置** | 遵循各语言社区公认命名惯例（Python PEP 8、TypeScript 标准、SQL 标准） |

#### 2.1.2 目录/包命名 —— 全小写，无分隔符

参照 Go package 命名规则：`all lowercase, no underscores, no hyphens`。

```
后端 Python 包目录：
  ✅ backend/services/          ✅ backend/models/
  ✅ backend/rag/retrieval/     ✅ backend/deepdoc/parser/
  ❌ backend/celery_tasks/      ❌ backend/user-services/

前端 TypeScript 目录：
  ✅ frontend/src/components/   ✅ frontend/src/hooks/
  ✅ frontend/src/app/(main)/   ✅ frontend/src/stores/
  ❌ frontend/src/myHooks/      ❌ frontend/src/UserComponents/
```

#### 2.1.3 文件命名 —— 全小写，下划线分隔

参照 Go file 命名规则：`all lowercase, underscore separated`。

| 技术栈 | 规则 | 示例 |
|--------|------|------|
| **Python** | snake_case | `user_service.py`, `document_tasks.py`, `auth_middleware.py` |
| **TypeScript** | kebab-case | `api-client.ts`, `auth-store.ts`, `security-level.ts` |
| **TypeScript 组件** | PascalCase.tsx | `DatasetCard.tsx`, `CitationCard.tsx`, `SecurityLevelPicker.tsx` |
| **SQL 脚本** | snake_case.sql | `init.sql`, `migration_001_add_tags.sql` |
| **配置文件** | 按平台惯例 | `.env`, `tsconfig.json`, `start_backend.bat` |

#### 2.1.4 类/结构体命名 —— PascalCase

| 语言 | 规则 | 示例 |
|------|------|------|
| **Python 类** | PascalCase | `BaseModel`, `User`, `HybridSearcher`, `RAGPipeline` |
| **TypeScript 组件** | PascalCase | `ChatWindow`, `AuditTable`, `FileUploader` |
| **TypeScript 接口/类型** | PascalCase | `User`, `Citation`, `AuthState`, `DatasetCreateRequest` |

#### 2.1.5 方法/函数命名 —— 动词前缀

| 语言 | 规则 | 示例 |
|------|------|------|
| **Python 方法** | snake_case，动词前缀 | `create_app()`, `get_user_by_id()`, `stream_answer()`, `_build_prompt()` |
| **TypeScript 函数** | camelCase，动词前缀 | `sendMessage()`, `useAuth()`, `handleSubmit()`, `getToken()` |
| **布尔返回值** | Is/Has/Can 前缀 | `is_active`, `has_permission()`, `can_access()` |

#### 2.1.6 枚举/常量命名

| 语言 | 规则 | 示例 |
|------|------|------|
| **Python 常量** | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT = 3`, `STATUS_ACTIVE = "active"` |
| **TypeScript 枚举** | PascalCase 枚举 + UPPER_SNAKE_CASE 成员 | `enum UserRole { SuperAdmin = 'super_admin' }` |
| **TypeScript 常量** | UPPER_SNAKE_CASE | `const SECURITY_LEVELS = [...]`, `const MAX_UPLOAD_SIZE = 200 * 1024 * 1024` |

#### 2.1.7 错误/异常命名

| 语言 | 规则 | 示例 |
|------|------|------|
| **Python 异常类** | PascalCase，Error 后缀 | `AuthError`, `DocumentParseError`, `TokenExpiredError` |
| **Python 异常实例** | snake_case | `raise AuthError("令牌无效")` |

#### 2.1.8 缩写词保持统一大小写

参照 Go 缩写词规则：当名称中包含标准缩写词时，该缩写词保持全大写或全小写（取决于位置）。

```
Python：
  ✅ LLMClient, HTTPHandler, ParseOFD, get_http_client
  ❌ LlmClient, HttpHandler, ParseOfd

TypeScript：
  ✅ LLMConfig, S3Uploader, parseJSON, getHTTPClient
  ❌ LlmConfig, S3Uploader (注意：缩写全大写)
  ❌ S3Uploader → ✅ S3Uploader (S3 全大写)

SQL：
  ✅ sso_uid, api_key_encrypted
  ❌ ssoUid, apiKeyEncrypted (SQL 统一 snake_case，缩写小写)
```

#### 2.1.9 SQL 命名规范（补充）

数据库对象命名遵循 SQL 标准惯例，与 Go/Python 的 snake_case 文件规则对齐。

| 对象类型 | 规则 | 示例 |
|----------|------|------|
| **表名** | 全小写，下划线分隔，复数形式 | `users`, `document_tags`, `chat_messages`, `qa_records` |
| **关联表** | 两表名单数+下划线连接 | `user_roles`（user_id ↔ role_id）|
| **字段名** | 全小写，下划线分隔，单数形式 | `tenant_id`, `password_hash`, `security_level`, `sso_uid` |
| **布尔字段** | `is_` 前缀 | `is_active`, `is_public`, `is_default` |
| **时间字段** | 动词/名词 + `_at` 后缀 | `created_at`, `updated_at`, `last_login_at`, `locked_until` |
| **外键字段** | 关联表单数 + `_id` 后缀 | `tenant_id`, `department_id`, `uploaded_by`（而非 `uploader_id`）|
| **主键** | 统一 `id`，CHAR(36) 类型 | `id CHAR(36) PRIMARY KEY DEFAULT (UUID())`()` |
| **JSON/JSON 字段** | 名词 snake_case | `config`, `permissions`, `citations`, `parse_config` |
| **主键约束** | 表名 + `_pkey`（PG 自动） | `users_pkey` |
| **唯一约束** | `uk_` + 字段名 | `uk_doc_tag`（document_tag_relations 表）|
| **索引名** | `idx_` + 表名 + 字段名 | `idx_users_tenant`, `idx_documents_dataset`, `idx_audit_created` |
| **外键约束** | 表名 + `_` + 字段 + `_fkey`（PG 自动） | `users_tenant_id_fkey` |

##### SQL 命名反例

```sql
-- ❌ 错误示例
CREATE TABLE DocumentTags (           -- 大写表名
    Id SERIAL PRIMARY KEY,            -- 大写字段，自增主键
    userId INT,                       -- camelCase
    documentTagName VARCHAR(100),     -- camelCase
    documentTag_type VARCHAR(50),     -- 混用分隔符
    createdAt TIMESTAMP               -- camelCase，缺少 _at 后缀规范
);

-- ✅ 正确示例
CREATE TABLE document_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL CHECK (type IN ('security_level', 'doc_type', 'year')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uk_document_tag UNIQUE (user_id, name)
);
CREATE INDEX idx_document_tags_type ON document_tags(type);
```

##### JSON/JSON 字段内部键命名

JSON/JSON 字段内部的键遵循 **snake_case**（与 SQL 列命名一致），API 序列化时前后端约定转换：

```
MySQL 存储：
  {"doc_id": "abc123", "content_snippet": "正文内容...", "score": 0.89}

Python 序列化后 API 响应保持 snake_case：
  { "doc_id": "...", "content_snippet": "...", "score": 0.89 }

TypeScript 接口定义（前端接收时手动映射或使用工具自动转换）：
  interface Citation {
    doc_id: string;          // snake_case，与 API 响应一致
    content_snippet: string;
    score: number;
  }
```

##### 枚举值命名

CHECK 约束中的枚举值使用 **snake_case**，与 SQL 字段命名一致：

```sql
-- ✅ 正确
role VARCHAR(50) CHECK (role IN ('super_admin', 'admin', 'user', 'auditor'))
status VARCHAR(50) CHECK (status IN ('pending', 'parsing', 'chunking', 'embedding', 'ready', 'error'))

-- ❌ 错误
role VARCHAR(50) CHECK (role IN ('superAdmin', 'Admin', 'USER'))
status VARCHAR(50) CHECK (role IN ('Pending', 'PARSING', 'ready'))
```

---

## 三、前端架构详设（Next.js 14 + App Router）

### 3.1 前端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Next.js | 14.x | SSR/SSG 框架，App Router |
| React | 18.x | UI 组件 |
| TypeScript | 5.x | 类型安全 |
| TailwindCSS | 3.x | 原子化样式 |
| Zustand | 4.x | 轻量状态管理 |
| Axios | 1.x | HTTP 请求 |
| React-Markdown | 9.x | Markdown 渲染 |
| React-Virtuoso | 4.x | 虚拟滚动列表 |
| date-fns | 3.x | 日期处理 |
| lucide-react | latest | 图标库 |

### 3.2 路由设计（App Router）

```
路由树                                 布局              鉴权      说明
───────────────────────────────────────────────────────────────────────────
/                                      根布局            公开      首页/登录跳转
├── /login                             (auth)/layout    公开      登录页
├── /sso-callback                      (auth)/layout    公开      SSO回调页
├── /dashboard                         (main)/layout    JWT       控制台首页
├── /datasets                          (main)/layout    JWT       数据集列表
│   └── /[id]                          (main)/layout    JWT       数据集详情
│       ├── /documents                 —                 —        文档列表
│       ├── /chunks                    —                 —        切片管理
│       ├── /testing                   —                 —        检索测试
│       └── /settings                  —                 —        配置
├── /chats                             (main)/layout    JWT       对话列表
│   └── /[id]                          (main)/layout    JWT       对话详情
├── /searches                          (main)/layout    JWT       检索列表
│   └── /[id]                          (main)/layout    JWT       检索详情
├── /files                             (main)/layout    JWT       文件管理
├── /models                            (main)/layout    JWT       模型配置
├── /admin                             (admin)/layout   Admin     管理员首页
│   ├── /users                         —                 —        用户管理
│   ├── /roles                         —                 —        角色管理
│   ├── /departments                   —                 —        部门管理
│   ├── /audit                         —                 —        审计日志
│   ├── /monitoring                    —                 —        系统监控
│   └── /settings                      —                 —        系统设置
```

### 3.3 布局设计

```
┌──────────────────────────────────────────────────────────────────┐
│  Header（顶部栏）                                                  │
│  [Logo]  知识库管理  [搜索框]  [用户头像▼]  [系统管理员入口]        │
├────────┬──────────────────────────────┬──────────────────────────┤
│Sidebar │     中间列（列表）            │    右侧列（详情/预览）      │
│        │                             │                          │
│数据集   │  [搜索] [+ 新建数据集]        │  数据集详情/对话窗口       │
│  └子集  │  ┌──────────────────┐       │                          │
│对话     │  │ 📁 公文数据集      │       │  ┌──────────────────┐    │
│检索     │  │ 128 文档 · 15k 切片│       │  │ 问答结果          │    │
│文件     │  ├──────────────────┤       │  │ 引用来源:          │    │
│模型     │  │ 📁 政策法规库     │       │  │ 📄 XX文件 §3.2    │    │
│        │  │ 56 文档 · 8k 切片  │       │  │ 📄 XX纪要 P12     │    │
│        │  └──────────────────┘       │  └──────────────────┘    │
│        │                             │                          │
├────────┴──────────────────────────────┴──────────────────────────┤
│  状态栏  © 2024 GovRAG  v1.0.0                                   │
└──────────────────────────────────────────────────────────────────┘
```

### 3.4 核心组件详设

#### 3.4.1 请求封装（api-client.ts）

```typescript
// frontend/src/lib/api-client.ts

import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { useAuthStore } from '@/stores/auth-store';
import { useAuditHook } from '@/hooks/useAudit';

const apiClient: AxiosInstance = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE || '/api/v1',
  timeout: 30000,
});

// 请求拦截器 —— JWT 鉴权 + 审计埋点
apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  // 审计日志自动记录请求信息（由 audit_middleware 在服务端处理）
  config.headers['X-Request-Id'] = crypto.randomUUID();
  config.headers['X-Request-Time'] = Date.now().toString();
  return config;
});

// 响应拦截器 —— Token 过期处理
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
      window.location.href = '/login';
    }
    // 涉密等级不足（403）
    if (error.response?.status === 403) {
      console.warn('权限不足：涉密等级不够');
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```

#### 3.4.2 涉密等级选择器（SecurityLevelPicker.tsx）

```typescript
// frontend/src/components/dataset/SecurityLevelPicker.tsx

'use client';

import { SECURITY_LEVELS, SecurityLevel } from '@/lib/security-level';

interface SecurityLevelPickerProps {
  value: SecurityLevel;
  maxLevel: SecurityLevel;        // 当前用户最大涉密等级
  onChange: (level: SecurityLevel) => void;
}

export function SecurityLevelPicker({ value, maxLevel, onChange }: SecurityLevelPickerProps) {
  return (
    <div className="flex gap-2">
      {SECURITY_LEVELS.filter(l => l.value <= maxLevel).map((level) => (
        <button
          key={level.value}
          onClick={() => onChange(level.value)}
          className={`px-3 py-1 text-sm rounded border transition
            ${value === level.value
              ? 'bg-red-50 border-red-400 text-red-700'
              : 'bg-white border-gray-200 text-gray-600 hover:border-gray-400'
            }`}
        >
          {level.label}
        </button>
      ))}
    </div>
  );
}
```

#### 3.4.3 溯源引用卡片（CitationCard.tsx）

```typescript
// frontend/src/components/chat/CitationCard.tsx

'use client';

interface Citation {
  doc_name: string;
  doc_id: string;
  chunk_id: string;
  page?: number;
  content_snippet: string;
  score: number;
}

interface CitationCardProps {
  citations: Citation[];
  onNavigate: (chunkId: string) => void;
}

export function CitationCard({ citations, onNavigate }: CitationCardProps) {
  return (
    <div className="mt-3 border-t border-gray-100 pt-3">
      <h4 className="text-xs font-semibold text-gray-500 mb-2">
        引用来源（{citations.length}）
      </h4>
      <div className="space-y-2">
        {citations.map((cite) => (
          <div
            key={cite.chunk_id}
            onClick={() => onNavigate(cite.chunk_id)}
            className="p-2 bg-blue-50/50 border border-blue-100 rounded cursor-pointer
                       hover:bg-blue-100 transition text-sm"
          >
            <div className="flex justify-between items-center mb-1">
              <span className="font-medium text-blue-800 truncate max-w-[70%]">
                {cite.doc_name}
              </span>
              <span className="text-xs text-blue-500">
                相关度 {(cite.score * 100).toFixed(0)}%
              </span>
            </div>
            <p className="text-xs text-gray-600 line-clamp-2">
              {cite.content_snippet}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
```

#### 3.4.4 对话窗口 + SSE 流式输出

```typescript
// frontend/src/hooks/useChat.ts

import { useState, useCallback } from 'react';
import { useChatStore } from '@/stores/chat-store';

export function useChat(chatId: string) {
  const [streaming, setStreaming] = useState(false);
  const { addMessage, updateMessage } = useChatStore();

  const sendMessage = useCallback(async (question: string) => {
    addMessage(chatId, { role: 'user', content: question });
    addMessage(chatId, { role: 'assistant', content: '', citations: [] });
    setStreaming(true);

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE}/chat/${chatId}/ask`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
          body: JSON.stringify({ question }),
        }
      );

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.slice(6));
            if (data.type === 'token') {
              updateMessage(chatId, (prev) => ({ ...prev, content: prev.content + data.text }));
            } else if (data.type === 'citations') {
              updateMessage(chatId, (prev) => ({ ...prev, citations: data.citations }));
            }
          }
        }
      }
    } finally {
      setStreaming(false);
    }
  }, [chatId]);

  return { sendMessage, streaming };
}
```

### 3.5 状态管理（Zustand）

```typescript
// frontend/src/stores/auth-store.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: string;
  username: string;
  real_name: string;
  role: string;            // 'super_admin' | 'admin' | 'user'
  security_level: number;  // 0-4
  department_id: string;
  tenant_id: string;
}

interface AuthState {
  token: string | null;
  refreshToken: string | null;
  user: User | null;
  login: (token: string, refreshToken: string, user: User) => void;
  logout: () => void;
  canAccess: (requiredLevel: number) => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      refreshToken: null,
      user: null,
      login: (token, refreshToken, user) => set({ token, refreshToken, user }),
      logout: () => set({ token: null, refreshToken: null, user: null }),
      canAccess: (requiredLevel) => {
        const user = get().user;
        return user ? user.security_level >= requiredLevel : false;
      },
    }),
    { name: 'govrag-auth' }
  )
);
```

---

## 四、后端架构详设（Flask + Celery + SQLAlchemy）

### 4.1 应用工厂

```python
# backend/app.py

from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate

from backend.config import get_config
from backend.models.base import db
from backend.api import register_blueprints
from backend.middleware import register_middlewares


def create_app(config_name: str = None) -> Flask:
    app = Flask(__name__)
    config = get_config(config_name)
    app.config.from_object(config)

    # 数据库
    db.init_app(app)
    Migrate(app, db)

    # 跨域（开发环境）
    CORS(app, origins=config.CORS_ORIGINS, supports_credentials=True)

    # 注册 Blueprint
    register_blueprints(app)

    # 注册中间件
    register_middlewares(app)

    return app
```

### 4.2 三层鉴权体系

```
┌─────────────────────────────────────────────────────────────────┐
│                    第一层：用户认证（Auth Layer）                  │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐   │
│  │ 用户名+密码   │    │ OAuth2.0 SSO │    │ API Key          │   │
│  │ bcrypt 加密   │    │ 政务统一平台  │    │ 服务间调用        │   │
│  └──────┬───────┘    └──────┬───────┘    └────────┬─────────┘   │
│         │                   │                     │              │
│         └───────────────────┼─────────────────────┘              │
│                             ▼                                    │
│                  ┌─────────────────────┐                         │
│                  │  JWT Token 签发      │                         │
│                  │  {                   │                         │
│                  │    sub: user_id,     │                         │
│                  │    tenant_id,        │                         │
│                  │    role,             │                         │
│                  │    security_level,   │                         │
│                  │    exp, iat          │                         │
│                  │  }                   │                         │
│                  └─────────────────────┘                         │
├─────────────────────────────────────────────────────────────────┤
│                  第二层：全局接口鉴权（API Middleware）            │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  @require_auth 装饰器                                     │   │
│  │  ├─ JWT 签名校验（RSA256）                                 │   │
│  │  ├─ 过期时间校验                                           │   │
│  │  ├─ Token 黑名单检查（Redis）                              │   │
│  │  ├─ 租户隔离：请求路径/参数中的 tenant_id 必须匹配          │   │
│  │  └─ 将 current_user 注入 flask.g                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  例外路由（白名单，无需鉴权）：                                    │
│  ├─ POST /api/v1/auth/login                                     │
│  ├─ GET  /api/v1/auth/sso/callback                              │
│  └─ GET  /api/v1/system/health                                  │
├─────────────────────────────────────────────────────────────────┤
│                  第三层：管理员后台鉴权（Admin Layer）             │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  @require_admin 装饰器                                    │   │
│  │  ├─ 校验 role ∈ ('super_admin', 'admin')                  │   │
│  │  ├─ 三员分立检查（系统管理员/安全保密员/安全审计员）          │   │
│  │  ├─ 所有 /admin/* 操作强制记录审计日志                      │   │
│  │  └─ 敏感操作二次密码确认                                    │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

#### 鉴权中间件实现

```python
# backend/middleware/auth_middleware.py

import functools
import jwt
from flask import request, g, jsonify, current_app
from datetime import datetime, timezone

from backend.models.user import User
from backend.utils.jwt_utils import decode_token, is_token_blacklisted


class AuthError(Exception):
    def __init__(self, message: str, status_code: int = 401):
        self.message = message
        self.status_code = status_code


def require_auth(f):
    """第二层：全局接口鉴权"""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        token = _extract_token()
        if not token:
            raise AuthError("缺少认证令牌", 401)

        if is_token_blacklisted(token):
            raise AuthError("令牌已失效", 401)

        try:
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            raise AuthError("令牌已过期", 401)
        except jwt.InvalidTokenError:
            raise AuthError("无效令牌", 401)

        user = User.query.get(payload['sub'])
        if not user or not user.is_active:
            raise AuthError("用户不存在或已禁用", 401)

        if user.tenant_id != payload.get('tenant_id'):
            raise AuthError("租户不匹配", 403)

        g.current_user = user
        g.tenant_id = user.tenant_id
        g.security_level = user.security_level
        g.role = user.role
        return f(*args, **kwargs)
    return decorated


def require_admin(f):
    """第三层：管理员后台鉴权"""
    @functools.wraps(f)
    @require_auth
    def decorated(*args, **kwargs):
        if g.role not in ('super_admin', 'admin'):
            raise AuthError("需要管理员权限", 403)
        return f(*args, **kwargs)
    return decorated


def require_security_level(min_level: int):
    """涉密等级控制"""
    def decorator(f):
        @functools.wraps(f)
        @require_auth
        def decorated(*args, **kwargs):
            if g.security_level < min_level:
                raise AuthError(f"需要涉密等级≥{min_level}", 403)
            return f(*args, **kwargs)
        return decorated
    return decorator


def _extract_token() -> str | None:
    """从请求头中提取 Token"""
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header[7:]
    return request.args.get('token')  # SSE 兼容
```

### 4.3 SQLAlchemy 数据模型

#### 基类

```python
# backend/models/base.py

import uuid
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID

db = SQLAlchemy()


class BaseModel(db.Model):
    __abstract__ = True

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class TenantModel(BaseModel):
    __abstract__ = True

    tenant_id = db.Column(UUID(as_uuid=True), nullable=False, index=True)
```

#### 核心模型

```python
# backend/models/user.py
from backend.models.base import db, TenantModel
from sqlalchemy.dialects.postgresql import UUID
import uuid

class User(TenantModel):
    __tablename__ = 'users'

    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    real_name = db.Column(db.String(100))                      # 真实姓名
    email = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    department_id = db.Column(UUID(as_uuid=True), nullable=True)
    role = db.Column(db.String(50), default='user')            # super_admin/admin/user/auditor
    security_level = db.Column(db.Integer, default=0)          # 0-4
    job_title = db.Column(db.String(100))                       # 职务
    sso_uid = db.Column(db.String(255), nullable=True)         # SSO统一认证ID
    is_active = db.Column(db.Boolean, default=True)
    last_login_at = db.Column(db.DateTime(timezone=True))
    password_changed_at = db.Column(db.DateTime(timezone=True))
    login_failed_count = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime(timezone=True), nullable=True)


# backend/models/document.py
class Document(TenantModel):
    __tablename__ = 'documents'

    dataset_id = db.Column(UUID(as_uuid=True), nullable=False, index=True)
    name = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(50))                        # pdf/word/excel/ofd/wps
    file_size = db.Column(db.BigInteger, default=0)
    file_path = db.Column(db.String(1000))                      # MinIO 对象路径
    status = db.Column(db.String(50), default='pending')        # pending/parsing/ready/error
    chunk_count = db.Column(db.Integer, default=0)
    token_count = db.Column(db.Integer, default=0)
    parse_config = db.Column(db.JSON)                           # 解析配置（切块大小、重叠等）

    # 政务字段
    security_level = db.Column(db.Integer, default=0)           # 涉密等级
    doc_type = db.Column(db.String(50))                         # 公文类型：通知/报告/批复/函
    doc_year = db.Column(db.String(10))                         # 年度
    issuing_org = db.Column(db.String(255))                     # 发文机关
    doc_number = db.Column(db.String(100))                      # 文号
    topic_words = db.Column(db.String(500))                     # 主题词

    uploaded_by = db.Column(UUID(as_uuid=True))


# backend/models/audit_log.py
class AuditLog(BaseModel):
    __tablename__ = 'audit_logs'

    tenant_id = db.Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = db.Column(UUID(as_uuid=True), nullable=False, index=True)
    username = db.Column(db.String(100))
    action = db.Column(db.String(100), nullable=False, index=True)  # login/logout/search/chat/upload/download/delete
    resource_type = db.Column(db.String(100))                       # document/dataset/chat/user
    resource_id = db.Column(UUID(as_uuid=True), nullable=True)
    resource_name = db.Column(db.String(500))
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    request_params = db.Column(db.JSON)
    response_status = db.Column(db.Integer)
    execution_time_ms = db.Column(db.Integer)
```

---

## 五、核心引擎设计

### 5.1 文档处理流水线（Document Pipeline）

```
document_service.py 文档处理主流程：

文档上传 → MinIO 存储 → Celery 异步任务 → 流水线处理

┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  上传文件  │───▶│  文件校验  │───▶│  格式解析  │───▶│  智能切块  │───▶│  向量嵌入  │
│           │    │ 类型/大小  │    │ deepdoc/  │    │ chunker/  │    │ embedding │
└──────────┘    │ 安全扫描   │    │ parser/   │    │           │    │ Infinity  │
                └──────────┘    └──────────┘    └──────────┘    └──────────┘
                                                                      │
                                                                      ▼
                                                              ┌──────────────┐
                                                              │ 状态回调       │
                                                              │ ready / error │
                                                              └──────────────┘
```

```python
# backend/rag/pipeline/rag_pipeline.py
# LCEL 风格 RAG 流水线

from dataclasses import dataclass, field
from typing import List, AsyncIterator
from backend.rag.retrieval.hybrid_search import HybridSearcher
from backend.rag.generation.context_assembler import ContextAssembler
from backend.rag.generation.llm_client import LLMClient


@dataclass
class RAGContext:
    """RAG 流水线上下文——贯穿整个流水线的状态对象"""
    question: str
    dataset_ids: List[str]
    chat_history: List[dict] = field(default_factory=list)
    retrieved_chunks: List[dict] = field(default_factory=list)
    merged_context: str = ""
    final_prompt: str = ""
    answer: str = ""
    citations: List[dict] = field(default_factory=list)


class RAGPipeline:
    """
    LCEL 风格 RAG 流水线
    每个步骤接收 RAGContext，修改后传递至下一步
    """

    def __init__(self, searcher: HybridSearcher, assembler: ContextAssembler, llm: LLMClient):
        self.searcher = searcher
        self.assembler = assembler
        self.llm = llm

    def run(self, question: str, dataset_ids: List[str],
            chat_history: List[dict] = None, security_level: int = 0) -> RAGContext:
        ctx = RAGContext(question=question, dataset_ids=dataset_ids,
                         chat_history=chat_history or [])

        # Step 1: 多路混合检索
        ctx = self._retrieve(ctx, security_level)

        # Step 2: 上下文拼接 + 溯源引用
        ctx = self._assemble(ctx)

        # Step 3: LLM 生成
        ctx = self._generate(ctx)

        return ctx

    async def run_stream(self, question: str, dataset_ids: List[str],
                         chat_history: List[dict] = None,
                         security_level: int = 0) -> AsyncIterator[str]:
        ctx = RAGContext(question=question, dataset_ids=dataset_ids,
                         chat_history=chat_history or [])
        ctx = self._retrieve(ctx, security_level)
        ctx = self._assemble(ctx)

        async for token in self.llm.stream_chat(ctx.final_prompt, ctx.chat_history):
            yield token

        # 流式结束后一次性发送引用
        yield f"__CITATIONS__:{json.dumps(ctx.citations)}"

    def _retrieve(self, ctx: RAGContext, security_level: int) -> RAGContext:
        """Step 1: 混合检索（向量 + 关键词 + RRF 融合 + 重排序）"""
        results = self.searcher.search(
            query=ctx.question,
            dataset_ids=ctx.dataset_ids,
            security_level=security_level,
            top_k=20,
        )
        ctx.retrieved_chunks = results
        return ctx

    def _assemble(self, ctx: RAGContext) -> RAGContext:
        """Step 2: 上下文拼接，构建 Prompt"""
        ctx.merged_context, ctx.citations = self.assembler.assemble(
            chunks=ctx.retrieved_chunks,
            question=ctx.question,
            max_tokens=4096,
        )
        ctx.final_prompt = self.assembler.build_prompt(
            context=ctx.merged_context,
            question=ctx.question,
            chat_history=ctx.chat_history,
        )
        return ctx

    def _generate(self, ctx: RAGContext) -> RAGContext:
        """Step 3: LLM 生成"""
        ctx.answer = self.llm.chat(ctx.final_prompt, ctx.chat_history)
        return ctx
```

### 5.2 混合检索模块

```python
# backend/rag/retrieval/hybrid_search.py

from backend.utils.infinity_client import InfinityClient
from backend.models.document import Document
from backend.models.chunk import Chunk
from sqlalchemy import and_


class HybridSearcher:
    """混合检索器：向量检索 + BM25 关键词 + RRF 融合 + 重排序"""

    def __init__(self, infinity_client: InfinityClient):
        self.infinity = infinity_client

    def search(self, query: str, dataset_ids: list[str],
               security_level: int = 0, top_k: int = 20) -> list[dict]:
        # 1. 向量检索（Infinity）
        vector_results = self.infinity.search(
            query_text=query,
            dataset_ids=dataset_ids,
            security_level=security_level,
            top_k=top_k * 2,
        )

        # 2. 关键词检索（BM25 —— PostgreSQL tsvector 或 Infinity 全文索引）
        keyword_results = self._keyword_search(query, dataset_ids, security_level, top_k * 2)

        # 3. Reciprocal Rank Fusion 融合
        fused = self._rrf_fusion(vector_results, keyword_results, k=60)

        # 4. 重排序（BGE-Reranker）
        reranked = self._rerank(query, fused, top_k)

        return reranked

    def _keyword_search(self, query: str, dataset_ids: list[str],
                        security_level: int, top_k: int) -> list[dict]:
        """BM25 关键词检索 —— PostgreSQL tsquery"""
        from backend.models.base import db
        from sqlalchemy import text

        ts_query = ' | '.join(query.split())
        sql = text("""
            SELECT c.id, c.content, c.document_id, c.chunk_index,
                   ts_rank(to_tsvector('simple', c.content), to_tsquery('simple', :query)) AS score
            FROM chunks c
            JOIN documents d ON c.document_id = d.id
            WHERE c.dataset_id = ANY(:dataset_ids)
              AND d.security_level <= :security_level
              AND to_tsvector('simple', c.content) @@ to_tsquery('simple', :tsquery)
            ORDER BY score DESC
            LIMIT :limit
        """)
        result = db.session.execute(sql, {
            'query': query,
            'tsquery': ts_query,
            'dataset_ids': dataset_ids,
            'security_level': security_level,
            'limit': top_k,
        })
        return [dict(row) for row in result]

    def _rrf_fusion(self, vec_results: list[dict], kw_results: list[dict],
                    k: int = 60) -> list[dict]:
        """RRF 融合算法"""
        scores = {}
        for rank, item in enumerate(vec_results):
            chunk_id = item['id']
            scores[chunk_id] = scores.get(chunk_id, 0) + 1.0 / (k + rank + 1)
        for rank, item in enumerate(kw_results):
            chunk_id = item['id']
            scores[chunk_id] = scores.get(chunk_id, 0) + 1.0 / (k + rank + 1)

        sorted_ids = sorted(scores, key=scores.get, reverse=True)
        all_items = {item['id']: item for item in vec_results + kw_results}
        return [all_items[cid] for cid in sorted_ids if cid in all_items]

    def _rerank(self, query: str, candidates: list[dict], top_k: int) -> list[dict]:
        """BGE-Reranker 重排序"""
        # 调用 BGE-Reranker cross-encoder 精排
        # 此处省略具体实现，返回重排后的 top_k 结果
        return candidates[:top_k]
```

### 5.3 LLM 调用客户端

```python
# backend/rag/generation/llm_client.py

import httpx
import json
from typing import AsyncIterator
from backend.config.llm_factories import get_model_config


class LLMClient:
    """多模型厂商统一调用客户端"""

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.config = get_model_config(tenant_id)

    def chat(self, prompt: str, history: list[dict] = None, **kwargs) -> str:
        """同步调用 LLM"""
        messages = self._build_messages(prompt, history)
        with httpx.Client(timeout=120) as client:
            response = client.post(
                f"{self.config['api_base']}/chat/completions",
                headers={"Authorization": f"Bearer {self.config['api_key']}"},
                json={
                    "model": self.config['model_name'],
                    "messages": messages,
                    "temperature": kwargs.get('temperature', 0.7),
                    "max_tokens": kwargs.get('max_tokens', 2048),
                }
            )
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']

    async def stream_chat(self, prompt: str, history: list[dict] = None,
                          **kwargs) -> AsyncIterator[str]:
        """流式调用 LLM —— SSE"""
        messages = self._build_messages(prompt, history)
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                'POST',
                f"{self.config['api_base']}/chat/completions",
                headers={"Authorization": f"Bearer {self.config['api_key']}"},
                json={
                    "model": self.config['model_name'],
                    "messages": messages,
                    "temperature": kwargs.get('temperature', 0.7),
                    "max_tokens": kwargs.get('max_tokens', 2048),
                    "stream": True,
                }
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith('data: '):
                        data_str = line[6:]
                        if data_str == '[DONE]':
                            break
                        data = json.loads(data_str)
                        delta = data.get('choices', [{}])[0].get('delta', {}).get('content', '')
                        if delta:
                            yield delta

    def _build_messages(self, prompt: str, history: list[dict] = None) -> list[dict]:
        messages = history or []
        messages.append({"role": "user", "content": prompt})
        return messages
```

### 5.4 上下文拼接器

```python
# backend/rag/generation/context_assembler.py

from typing import List, Tuple


class ContextAssembler:
    """上下文拼接 + 溯源引用构建"""

    def __init__(self, max_context_tokens: int = 4096):
        self.max_context_tokens = max_context_tokens

    def assemble(self, chunks: List[dict], question: str,
                 max_tokens: int = 4096) -> Tuple[str, List[dict]]:
        """
        拼接检索结果，构建上下文文本和溯源引用列表
        """
        context_parts = []
        citations = []
        token_count = 0

        for i, chunk in enumerate(chunks):
            part = self._format_chunk(i + 1, chunk)
            est_tokens = len(part) // 3  # 粗略估算 token 数

            if token_count + est_tokens > max_tokens:
                break

            context_parts.append(part)
            token_count += est_tokens
            citations.append({
                "doc_id": chunk.get("document_id"),
                "doc_name": chunk.get("doc_name", f"文档-{chunk.get('document_id', '')[:8]}"),
                "chunk_id": chunk.get("id"),
                "chunk_index": chunk.get("chunk_index"),
                "content_snippet": chunk["content"][:200],
                "score": chunk.get("score", 0.0),
            })

        context = "\n\n---\n\n".join(context_parts)
        return context, citations

    def _format_chunk(self, index: int, chunk: dict) -> str:
        """格式化单个切片为引用格式"""
        doc_name = chunk.get('doc_name', f"文档-{chunk.get('document_id', '')[:8]}")
        return (
            f"【引用来源 {index}】—— 《{doc_name}》\n"
            f"{chunk['content']}"
        )

    def build_prompt(self, context: str, question: str,
                     chat_history: List[dict] = None) -> str:
        """构建完整 Prompt"""
        system_prompt = (
            "你是政府机关内部知识库智能问答助手。请严格基于以下参考文档的内容回答问题。\n"
            "要求：\n"
            "1. 回答应准确、严谨，引用原文关键内容\n"
            "2. 如参考文档无法回答，请明确说明"该问题在现有知识库中未找到相关信息"\n"
            "3. 回答中涉及法规政策时需注明文号\n"
            "4. 保持正式、规范的公文语言风格\n"
            "5. 不得编造、推测或引用外部信息"
        )

        history_text = ""
        if chat_history:
            recent = chat_history[-6:]  # 最近 3 轮对话
            history_text = "\n".join(
                f"{'用户' if m['role']=='user' else '助手'}: {m['content'][:200]}"
                for m in recent
            )

        prompt = f"""{system_prompt}

{history_text}

参考文档：
{context}

用户问题：{question}

回答："""
        return prompt
```

---

## 六、API 接口设计

### 6.1 统一响应格式

```python
# backend/utils/response.py

from flask import jsonify
from typing import Any


def success(data: Any = None, message: str = "ok") -> tuple:
    return jsonify({"code": 0, "message": message, "data": data}), 200

def paginated(items: list, total: int, page: int, page_size: int) -> tuple:
    return jsonify({
        "code": 0,
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }
    }), 200

def error(message: str, code: int = 400) -> tuple:
    return jsonify({"code": -1, "message": message}), code
```

### 6.2 接口清单

```
认证接口 /api/v1/auth/
──────────────────────────────────────────────────────────────────
POST   /login                 用户名+密码登录          → {token, refresh_token, user}
POST   /logout                登出                     → {}
POST   /refresh-token         刷新Token                → {token, refresh_token}
GET    /sso/config            获取SSO配置              → {authorize_url, client_id}
GET    /sso/callback          SSO回调                  → 重定向至首页（附带token）
GET    /me                    获取当前用户信息          → {id, username, role, security_level}

数据集接口 /api/v1/datasets/
──────────────────────────────────────────────────────────────────
GET    /                      数据集列表（分页）        → paginated
POST   /                      创建数据集               → dataset
GET    /:id                   数据集详情               → dataset
PUT    /:id                   更新数据集               → dataset
DELETE /:id                   删除数据集               → {}
GET    /:id/documents         数据集文档列表            → paginated

文档接口 /api/v1/datasets/:id/documents/
──────────────────────────────────────────────────────────────────
POST   /upload                上传文档（multipart）    → document
GET    /:doc_id               文档详情                 → document
DELETE /:doc_id               删除文档                 → {}
PUT    /:doc_id/tags          更新文档标签             → document
PUT    /:doc_id/security      更新涉密等级             → document
POST   /batch-tag             批量打标签               → {success_count, fail_count}
POST   /batch-security        批量修改涉密等级          → {success_count, fail_count}

切片接口 /api/v1/documents/:doc_id/chunks/
──────────────────────────────────────────────────────────────────
GET    /                      切片列表（分页）          → paginated
GET    /:chunk_id             切片详情                 → chunk

对话接口 /api/v1/chats/
──────────────────────────────────────────────────────────────────
GET    /                      对话列表（分页）          → paginated
POST   /                      创建新对话               → chat
GET    /:id                   对话详情+消息列表         → chat + messages
DELETE /:id                   删除对话                 → {}
POST   /:id/ask               发送问题（SSE 流式）     → SSE stream
GET    /:id/export            导出对话记录             → CSV/JSON file

检索接口 /api/v1/search/
──────────────────────────────────────────────────────────────────
POST   /                      执行检索                 → {chunks, total}
GET    /history               检索历史                 → paginated

文件接口 /api/v1/files/
──────────────────────────────────────────────────────────────────
GET    /                      文件列表                 → paginated
POST   /upload                上传文件                 → file
DELETE /:id                   删除文件                 → {}

模型接口 /api/v1/models/
──────────────────────────────────────────────────────────────────
GET    /providers             支持的模型厂商列表        → providers
GET    /configs               当前租户模型配置          → configs
POST   /configs               创建模型配置             → config
PUT    /:id                   更新模型配置             → config
DELETE /:id                   删除模型配置             → {}
PUT    /:id/default           设为默认模型             → config

管理员接口 /api/v1/admin/
──────────────────────────────────────────────────────────────────
用户管理
GET    /users                 用户列表（分页）          → paginated
POST   /users                 创建用户                 → user
PUT    /users/:id             编辑用户                 → user
DELETE /users/:id             删除用户                 → {}
PUT    /users/:id/reset-password  重置密码             → {}

角色管理
GET    /roles                 角色列表                 → roles
POST   /roles                 创建角色                 → role
PUT    /roles/:id             编辑角色                 → role
DELETE /roles/:id             删除角色                 → {}

部门管理
GET    /departments           部门树形列表              → tree
POST   /departments           创建部门                 → dept
PUT    /departments/:id       编辑部门                 → dept
DELETE /departments/:id       删除部门                 → {}

审计日志
GET    /audit-logs            审计日志列表（分页+筛选）  → paginated
GET    /audit-logs/:id        审计日志详情              → log
GET    /audit-logs/export     导出审计日志              → CSV

问答记录
GET    /qa-records            问答记录列表（分页+筛选）  → paginated
GET    /qa-records/:id        问答记录详情              → record
GET    /qa-records/export     导出问答记录              → CSV

统计 /api/v1/admin/stats/
──────────────────────────────────────────────────────────────────
GET    /dashboard             仪表盘统计                → {users, datasets, docs, qa_count...}
GET    /qa                    问答统计（按日期/部门）     → stats
GET    /documents             文档统计（按类型/等级）     → stats

系统配置 /api/v1/admin/system/
──────────────────────────────────────────────────────────────────
GET    /settings              获取系统配置              → settings
PUT    /settings              更新系统配置              → settings
GET    /health                健康检查                  → {status, version}
```

### 6.3 接口示例

```python
# backend/api/v1/chat.py
# SSE 流式对话接口

from flask import Blueprint, request, Response, g, stream_with_context
from backend.middleware.auth_middleware import require_auth
from backend.services.chat_service import ChatService

chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/<chat_id>/ask', methods=['POST'])
@require_auth
def ask_question(chat_id: str):
    """流式问答接口 —— SSE"""
    data = request.get_json()
    question = data.get('question', '').strip()
    if not question:
        return error("问题不能为空", 400)

    service = ChatService()
    chat = service.get_chat(chat_id, g.tenant_id)
    if not chat:
        return error("对话不存在", 404)

    # 校验涉密数据集访问权限
    if not service.check_security_access(chat, g.security_level):
        return error("涉密等级不足，无权访问该对话关联的数据集", 403)

    def generate():
        audit_id = service.log_qa_start(chat_id, question, g)
        full_answer = ""
        citations = None

        try:
            for token in service.stream_answer(chat_id, question, g):
                full_answer += token
                yield f"data: {json.dumps({'type': 'token', 'text': token})}\n\n"

            # 流式结束后发送引用
            citations = service.get_last_citations(chat_id)
            yield f"data: {json.dumps({'type': 'citations', 'citations': citations})}\n\n"
            yield "data: [DONE]\n\n"

        finally:
            service.log_qa_end(audit_id, full_answer, citations, g)

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',  # Nginx 禁用缓冲
        }
    )
```

---


## 七、本地部署指南

### 7.1 环境准备

所有组件均在 Windows 宿主机本地直接运行，无需 Docker。

| 组件 | 安装方式 | 默认端口 | 首次配置 |
|------|----------|----------|----------|
| MySQL 8.0 | 官网安装包或已有服务 | 3306 | 创建库 `office_ragflow`，用户 root/123456 |
| Redis 7 | 下载 `redis-server.exe` 或 WSL `apt install redis` | 6379 | 配置 `requirepass redis123` |
| MinIO | 下载 `minio.exe` 直接运行 | 9000（API）/ 9001（控制台） | 用户 minioadmin / minioadmin |
| Infinity | 从 GitHub Release 下载 `infinity.exe` | 23817 | 直接运行即可 |

### 7.2 启动顺序

```powershell
# 1. 确保 MySQL、Redis、MinIO、Infinity 均已启动（各自打开一个终端或注册为 Windows 服务）

# 2. （一次性）初始化数据库
cd backend
pip install -r requirements.txt
python scripts/init_db.py

# 3. 启动 Flask 后端（终端 1）
python app.py

# 4. 启动 Celery Worker（终端 2）
celery -A celery_app worker -l info -P solo

# 5. 启动 Next.js 前端（终端 3）
cd ../frontend
npm install
npm run dev
```

### 7.3 验证清单

| 检查项 | 命令/操作 | 预期结果 |
|--------|-----------|----------|
| Flask 健康检查 | `curl localhost:5000/api/v1/system/health` | mysql/redis/minio 三绿 |
| 数据库建表 | `mysql -uroot -p123456 office_ragflow -e "SHOW TABLES;"` | 14 张表 |
| MinIO Bucket | 浏览器打开 `http://localhost:9001`，登录后查看 | `govrag` bucket 存在 |
| 前端页面 | 浏览器打开 `http://localhost:3000` | 显示首页 |

### 7.4 Windows 启动脚本

以下 `.bat` 脚本放在项目根目录，双击即可启动各组件：

```batch
:: scripts/start_backend.bat
cd /d %~dp0..\backend
python app.py
```

```batch
:: scripts/start_worker.bat
cd /d %~dp0..\backend
celery -A celery_app worker -l info -P solo
```

```batch
:: scripts/start_frontend.bat
cd /d %~dp0..\frontend
npm run dev
```

## 八、国产化适配

| 适配项 | 实现方案 |
|--------|----------|
| **OFD 版式文档** | `deepdoc/parser/ofd_parser.py` 扩展解析器，支持公文印章、版记识别 |
| **WPS 格式** | `deepdoc/parser/wps_parser.py` 扩展 .wps/.et/.dps 格式解析 |
---

## 九、安全增强清单

| 安全项 | 实现 | 优先级 |
|--------|------|--------|
| **三员分立** | `role` 字段区分 super_admin / admin / security_officer / auditor | P0 |
| **密码策略** | 复杂度正则、90天过期、5次失败锁定30分钟 | P0 |
| **会话超时** | JWT 有效期 2h + Refresh Token 7d，活跃检测 | P1 |
| **涉密等级数据过滤** | `document.security_level <= user.security_level` 全局 SQL 条件注入 | P0 |
| **审计日志** | 所有 CRUD + 登录/登出 + 问答操作自动记录 | P0 |
| **数据脱敏** | 检索预览中手机号/身份证号/邮箱自动打码 | P1 |
| **水印追溯** | 前端 WatermarkOverlay 组件（用户姓名+工号+时间戳） | P1 |
| **敏感词过滤** | 问答输出后置过滤中间件，匹配规则可配置 | P1 |
| **API 频率限制** | Redis 滑动窗口限流（登录 10次/min、Chat 30次/min） | P1 |
| **HTTPS 强制** | Nginx 301 重定向 + HSTS 头 | P0 |
| **文件安全** | 上传文件 MIME 校验 + 病毒扫描 ClamAV（可选） | P2 |

---

## 十、实施路线图

```
Phase 1: 基础骨架（4周）
────────────────────────────────────────────────────────
W1  ├─ 项目初始化：Next.js 14 脚手架 + Flask 工厂模式 + 本地服务启动
    ├─ 数据库：SQLAlchemy 模型定义 + Alembic 迁移 + init.sql
    └─ 基础设施：Redis / MinIO / Infinity / Nginx 配置

W2  ├─ 鉴权模块：JWT 签发/校验 + 三层鉴权中间件 + SSO OAuth2 对接
    ├─ 前端登录页 + SSO 回调页 + Zustand auth-store
    └─ API：/auth/login、/auth/sso/callback、/auth/me

W3  ├─ 数据集模块：CRUD + 前端列表页 + 详情页三栏布局
    ├─ 文件上传模块：MinIO 分片上传 + 前端拖拽上传组件
    └─ API：/datasets/*、/files/*

W4  ├─ 模型配置模块：厂商+模型 CRUD + llm_factories.json 解析
    ├─ 前端模型管理页面
    └─ 联调测试：本地全栈联调通过

Phase 2: RAG 引擎（4周）
────────────────────────────────────────────────────────
W5  ├─ 文档解析：deepdoc/ PDF/Word/Excel 解析器实现
    ├─ 切块模块：固定大小 + 语义切块 + 公文结构化切块
    └─ Celery 异步任务：文档解析 → 切块 → 向量化流水线

W6  ├─ Infinity 向量库集成：建表、写入、检索
    ├─ 混合检索：向量 + BM25 PostgreSQL tsvector + RRF 融合
    └─ BGE-Reranker 重排序集成

W7  ├─ LCEL-RAG 流水线：RAGPipeline + ContextAssembler + PromptBuilder
    ├─ LLM 多模型客户端：统一 API 流式/非流式调用
    └─ API：/chat/:id/ask SSE 流式接口

W8  ├─ 前端对话窗口：ChatWindow + SSE Reader + 流式渲染
    ├─ 溯源引用卡片：CitationCard + 切片跳转导航
    └─ 检索 API：/search + 前端检索页面

Phase 3: 政务增强（4周）
────────────────────────────────────────────────────────
W9  ├─ 涉密等级：SecurityLevelPicker + 数据级 SQL 权限过滤
    ├─ 公文标签：DocumentTag CRUD + TagSelector 前端组件
    └─ API：/documents/:id/tags、/batch-tag、/batch-security

W10 ├─ 部门管理：Department 树形 CRUD + DeptTree 前端组件
    ├─ 用户管理增强：部门绑定 + 涉密等级 + 三员角色分配
    └─ 角色权限：RBAC permissions JSONB

W11 ├─ 审计日志：AuditLog 自动埋点 + audit_middleware
    ├─ 问答记录：QARecord 表 + 满意度反馈
    ├─ 审计前端页：AuditTable + 按时间/操作/用户筛选 + CSV 导出
    └─ 使用统计：仪表盘聚合统计

W12 ├─ 安全增强：敏感词过滤、水印遮罩、频率限制
    ├─ 数据脱敏：手机号/身份证号脱敏工具
    └─ 国产适配：360/奇安信浏览器测试 + 国产模型联调

Phase 4: 测试与交付（3周）
────────────────────────────────────────────────────────
W13 ├─ 功能测试：全功能回归 + 边界测试
    ├─ 性能测试：向量检索并发压测、文档批量处理吞吐
    └─ 安全测试：OWASP Top 10 + 渗透测试

W14 ├─ 国产生态测试：Kylin/UOS + ARM64 + OceanBase 部署验证
    ├─ OFD/WPS 解析补充测试
    └─ 用户验收测试（UAT）

W15 ├─ 部署文档：本地部署指南 + 离线安装脚本
    ├─ 运维文档：日志管理、备份恢复、监控告警
    └─ v1.0.0 正式发布
```

---

## 十一、环境变量配置

```bash
# .env.example

# ========== 数据库 ==========
DB_PASSWORD=govrag_secure_password_2024

# ========== Redis ==========
REDIS_PASSWORD=redis_secure_password

# ========== MinIO ==========
MINIO_USER=govrag_minio
MINIO_PASSWORD=minio_secure_password

# ========== 应用密钥 ==========
JWT_SECRET_KEY=change-this-to-a-random-64-char-string
JWT_ALGORITHM=RS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=120
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# ========== SSO 单点登录 ==========
SSO_ENABLED=false
SSO_CLIENT_ID=
SSO_CLIENT_SECRET=
SSO_AUTHORIZE_URL=
SSO_TOKEN_URL=
SSO_USERINFO_URL=
SSO_LOGOUT_URL=

# ========== 审计 ==========
AUDIT_LOG_ENABLED=true
AUDIT_LOG_RETENTION_DAYS=180

# ========== 安全 ==========
SECURITY_LEVEL_ENABLED=true
LOGIN_MAX_FAILED_ATTEMPTS=5
LOGIN_LOCK_MINUTES=30
PASSWORD_EXPIRE_DAYS=90

# ========== 敏感词 ==========
SENSITIVE_WORD_FILTER_ENABLED=false
SENSITIVE_WORD_DICT_PATH=/data/sensitive_words.txt

# ========== 水印 ==========
WATERMARK_ENABLED=false

# ========== 前端 ==========
NEXT_PUBLIC_API_BASE=/api/v1
NEXT_PUBLIC_APP_NAME=政务智能知识库
NEXT_PUBLIC_SSO_ENABLED=false
```

---


## 附录 A：关键技术决策记录

| 决策 | 选择 | 理由 |
|------|------|------|
| ORM | SQLAlchemy 2.x | 替代 Peewee，社区更大，Alembic 迁移体系成熟，国产数据库 dialect 生态好 |
| 向量库 | Infinity | 对齐 RAGFlow 原生技术栈，性能优异，无外部依赖 |
| 对象存储 | MinIO | 与 RAGFlow 一致，S3 兼容，内网离线部署友好 |
| 前端框架 | Next.js 14 App Router | 对齐 RAGFlow React 生态，SSR 适配国产浏览器 SEO 需求 |
| 状态管理 | Zustand | 轻量，无 Provider 嵌套，与 RAGFlow 原生一致 |
| 异步任务 | Celery + Redis | 对齐 RAGFlow 架构，文档处理流水线成熟方案 |
| 国产数据库 | MySQL优先|SQLAlchemy 无适配成本，已有生产部署案例 |

## 附录 B：Reference —— RAGFlow 核心逻辑复刻清单

| RAGFlow 源文件 | GovRAG 复刻位置 | 复刻内容 |
|---------------|----------------|---------|
| `api/apps/auth/` 鉴权装饰器 | `backend/middleware/auth_middleware.py` | 三层鉴权：JWT 签发/校验 + Admin + 租户隔离 |
| `rag/retrieval/` 检索模块 | `backend/rag/retrieval/` | 混合检索 pipeline：向量 + BM25 + RRF + Reranker |
| `rag/prompts/` Prompt 模板 | `backend/rag/prompts/` | QA/Summary/System prompt JSON |
| `rag/llm/` LLM 调用 | `backend/rag/generation/llm_client.py` | 多厂商统一客户端 + SSE 流式 |
| `deepdoc/parser/` 文档解析 | `backend/deepdoc/parser/` | PDF/Word/Excel 解析器核心逻辑 |
| `conf/llm_factories.json` | `backend/config/llm_factories.json` | 模型厂商配置（扩展国产模型） |
| `api/apps/restful_apis/chat_api.py` | `backend/api/v1/chat.py` | SSE 流式对话接口 |
| `api/apps/restful_apis/dataset_api.py` | `backend/api/v1/dataset.py` | 数据集 CRUD |
| `api/apps/restful_apis/document_api.py` | `backend/api/v1/document.py` | 文档上传/管理 |
| `web/src/pages/next-chats/` | `frontend/src/app/(main)/chats/` | 对话窗口 + 溯源引用 UI |
| `web/src/pages/dataset/` | `frontend/src/app/(main)/datasets/` | 知识库三栏布局 |
