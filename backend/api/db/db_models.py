"""核心数据模型。

这里定义租户、用户、数据集、文件、文档等实体，是后端业务链路的事实来源。
"""

import uuid
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.types import TypeDecorator, CHAR
from werkzeug.security import generate_password_hash, check_password_hash


class GUID(TypeDecorator):
    """MySQL CHAR(36) ↔ Python UUID 自动转换"""
    impl = CHAR(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return str(value) if value else None

    def process_result_value(self, value, dialect):
        return uuid.UUID(value) if value else None

db = SQLAlchemy()


class BaseModel(db.Model):
    __abstract__ = True

    # 所有业务表都使用统一主键和时间戳字段。
    id = db.Column(GUID(), primary_key=True, default=uuid.uuid4)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        # 导出给前端时统一做 UUID 字符串化和敏感字段过滤。
        result = {}
        for c in self.__table__.columns:
            value = getattr(self, c.name)
            if isinstance(value, uuid.UUID):
                value = str(value)
            # 隐藏敏感字段
            if c.name == "password_hash":
                continue
            result[c.name] = value
        return result

# 租户基类：所有业务数据都通过 tenant_id 做隔离。
class TenantModel(BaseModel):
    __abstract__ = True
    tenant_id = db.Column(GUID(), nullable=False, index=True)


# ==================== 租户表 ====================

class Tenant(BaseModel):
    __tablename__ = "tenants"

    name = db.Column(db.String(255), nullable=False)
    code = db.Column(db.String(100), unique=True, nullable=False)
    status = db.Column(db.String(50), default="active")
    config = db.Column(db.JSON, default=dict)


# ==================== 用户表 ====================

class User(TenantModel):
    __tablename__ = "users"

    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    real_name = db.Column(db.String(100))
    email = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    department_id = db.Column(GUID(), nullable=True)
    role = db.Column(db.String(50), default="user")
    security_level = db.Column(db.Integer, default=0)
    job_title = db.Column(db.String(100))
    sso_uid = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    last_login_at = db.Column(db.DateTime(timezone=True))
    password_changed_at = db.Column(db.DateTime(timezone=True))
    login_failed_count = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime(timezone=True), nullable=True)

    @staticmethod
    def hash_password(password):
        return generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)


# ==================== 数据集表（知识库）====================

class Dataset(TenantModel):
    __tablename__ = "datasets"

    # 数据集就是知识库的逻辑容器，保存切分和向量化相关配置。
    name = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    embedding_model = db.Column(db.String(255), nullable=False)
    chunk_size = db.Column(db.Integer, default=512)
    chunk_overlap = db.Column(db.Integer, default=50)
    parser_config = db.Column(db.JSON, default=dict)
    security_level = db.Column(db.Integer, default=0)
    is_public = db.Column(db.Boolean, default=False)
    allowed_dept_ids = db.Column(db.JSON, default=dict)
    document_count = db.Column(db.Integer, default=0)
    chunk_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(50), default="active")
    created_by = db.Column(GUID())

    # 删除数据集时自动级联删除文档，避免孤儿记录。
    documents = db.relationship("Document", backref="dataset", cascade="all, delete-orphan")


# ==================== 文件表（MinIO 对象）====================

class File(TenantModel):
    __tablename__ = "files"

    # File 只记录对象存储里的原始文件，不直接承担文档语义。
    user_id = db.Column(GUID(), nullable=False)
    original_name = db.Column(db.String(500), nullable=False)
    object_key = db.Column(db.String(1000), nullable=False)
    file_size = db.Column(db.BigInteger, default=0)
    mime_type = db.Column(db.String(255))
    bucket_name = db.Column(db.String(255), default="govrag")


# ==================== 文档表 ====================

class Document(TenantModel):
    __tablename__ = "documents"

    # Document 把上传文件纳入某个数据集，是后续解析和索引的业务单元。
    dataset_id = db.Column(GUID(), db.ForeignKey("datasets.id"), nullable=False, index=True)
    name = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(50))
    file_size = db.Column(db.BigInteger, default=0)
    file_path = db.Column(db.String(1000))
    status = db.Column(db.String(50), default="pending")
    chunk_count = db.Column(db.Integer, default=0)
    token_count = db.Column(db.Integer, default=0)
    parse_config = db.Column(db.JSON, default=dict)
    security_level = db.Column(db.Integer, default=0)
    doc_type = db.Column(db.String(50))
    doc_year = db.Column(db.String(10))
    issuing_org = db.Column(db.String(255))
    doc_number = db.Column(db.String(100))
    topic_words = db.Column(db.String(500))
    uploaded_by = db.Column(GUID())
