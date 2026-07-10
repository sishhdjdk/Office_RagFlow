# 项目命名规范

本项目涵盖 Python（后端）和 TypeScript（前端）两个技术栈，命名规范在核心原则对齐的基础上适配各自语言惯例。

## 1. 核心原则

| 原则 | 说明 |
|------|------|
| **一致性优先** | 同一技术栈内的命名风格必须统一，禁止混用 |
| **语义明确** | 命名应直接表达意图，避免歧义缩写（`department` 优于 `dept` 除非上下文明确） |
| **约定优于配置** | 遵循各语言社区公认命名惯例（Python PEP 8、TypeScript/React 社区标准） |

## 2. 目录命名 —— 全小写，无分隔符

```
后端 Python 包目录：
  ✅ backend/services/          ✅ backend/models/
  ✅ backend/rag/retrieval/     ✅ backend/deepdoc/parser/
  ❌ backend/celery_tasks/      ❌ backend/user-services/

前端 TypeScript 目录：
  ✅ frontend/components/       ✅ frontend/hooks/
  ✅ frontend/app/(main)/       ✅ frontend/stores/
  ❌ frontend/myHooks/          ❌ frontend/UserComponents/
```

## 3. 文件命名

| 技术栈 | 规则 | 示例 |
|--------|------|------|
| **Python** | snake_case（全小写，下划线分隔） | `user_service.py`、`document_tasks.py`、`auth_middleware.py` |
| **TypeScript 工具/模块** | kebab-case（全小写，连字符分隔） | `api-client.ts`、`auth-store.ts`、`security-level.ts` |
| **TypeScript 组件** | PascalCase.tsx | `DatasetCard.tsx`、`AuditTable.tsx`、`SecurityLevelPicker.tsx` |
| **配置文件** | 按平台惯例 | `.env`、`tsconfig.json`、`start_backend.bat` |

## 4. 类/组件/接口命名 —— PascalCase

| 语言 | 规则 | 示例 |
|------|------|------|
| **Python 类** | PascalCase | `BaseModel`、`User`、`HybridSearcher` |
| **TypeScript 组件** | PascalCase | `ChatWindow`、`AuditTable`、`FileUploader` |
| **TypeScript 接口/类型** | PascalCase | `User`、`Citation`、`AuthState`、`DatasetCreateRequest` |

## 5. 函数/方法命名 —— 动词前缀

| 语言 | 规则 | 示例 |
|------|------|------|
| **Python 函数** | snake_case，动词前缀 | `create_app()`、`get_user_by_id()`、`stream_answer()` |
| **Python 私有方法** | `_` 前缀 | `_build_prompt()`、`_validate_token()` |
| **TypeScript 函数** | camelCase，动词前缀 | `sendMessage()`、`handleSubmit()`、`getToken()` |
| **React Hook** | `use` 前缀 | `useAuth()`、`useChat()`、`useDataset()` |
| **布尔返回值** | Is/Has/Can 前缀 | `is_active`、`has_permission()`、`can_access()` |

## 6. 常量/枚举命名

| 语言 | 规则 | 示例 |
|------|------|------|
| **Python 常量** | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT = 3`、`STATUS_ACTIVE = "active"` |
| **TypeScript 枚举** | PascalCase 枚举名，枚举成员 snake_case 字符串值 | `enum UserRole { SuperAdmin = 'super_admin' }` |
| **TypeScript 常量** | UPPER_SNAKE_CASE | `const SECURITY_LEVELS = [...]`、`const MAX_UPLOAD_SIZE = 200 * 1024 * 1024` |

## 7. 错误/异常命名

| 语言 | 规则 | 示例 |
|------|------|------|
| **Python 异常类** | PascalCase，Error 后缀 | `AuthError`、`DocumentParseError` |
| **Python 异常实例** | snake_case | `raise AuthError("令牌无效")` |

## 8. 缩写词保持统一大小写

当名称中包含标准缩写词时，该缩写词保持全大写或全小写（取决于位置）。

```
Python：
  ✅ LLMClient、HTTPHandler、ParseOFD、get_http_client
  ❌ LlmClient、HttpHandler、ParseOfd

TypeScript：
  ✅ LLMConfig、S3Uploader、parseJSON、getHTTPClient
  ❌ LlmConfig、parseJson
```

## 9. SQL 命名规范

| 对象 | 规则 | 示例 |
|------|------|------|
| **表名** | 全小写，下划线分隔，复数形式 | `users`、`document_tags`、`chat_messages` |
| **字段名** | 全小写，下划线分隔 | `tenant_id`、`password_hash`、`security_level` |
| **布尔字段** | `is_` 前缀 | `is_active`、`is_public`、`is_default` |
| **时间字段** | `_at` 后缀 | `created_at`、`updated_at`、`last_login_at` |
| **外键** | 关联表单数 + `_id` 后缀 | `tenant_id`、`department_id` |
| **主键** | 统一 `id` | `id CHAR(36) PRIMARY KEY` |
| **索引** | `idx_` + 表名 + 字段名 | `idx_users_tenant`、`idx_audit_created` |

## 10. 速查表

| 类型 | Python | TypeScript |
|------|--------|------------|
| 包/目录 | `snake_case`（全小写无分隔符） | `kebab-case`（全小写无分隔符） |
| 文件 | `snake_case.py` | `kebab-case.ts` / `PascalCase.tsx` |
| 类/组件 | `PascalCase` | `PascalCase` |
| 函数/方法 | `snake_case` | `camelCase` |
| 常量 | `UPPER_SNAKE_CASE` | `UPPER_SNAKE_CASE` |
| 私有成员 | `_` 前缀 | `private` 关键字 |
| 布尔值 | `is_` / `has_` 前缀 | `is` / `has` 前缀 |
