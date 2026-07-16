import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()


class Config:
    """基础配置，所有环境共用。"""

    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-change-me")

    # MySQL 数据库
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "123456")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "3306")
    DB_NAME: str = os.getenv("DB_NAME", "office_ragflow")
    SQLALCHEMY_DATABASE_URI: str = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        "?charset=utf8mb4"
    )

    # Redis 缓存
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://:redis123@localhost:6379/0")

    # MinIO 对象存储
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    MINIO_BUCKET: str = os.getenv("MINIO_BUCKET", "govrag")

    # Infinity 向量库
    INFINITY_HOST: str = os.getenv("INFINITY_HOST", "localhost")
    INFINITY_PORT: int = int(os.getenv("INFINITY_PORT", "23817"))

    # JWT 鉴权
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 120

    # 跨域配置
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:3000")

    def get(self, key: str, default: Any = None) -> Any:
        """安全获取配置项，失败时返回默认值。"""
        try:
            return getattr(self, key)
        except AttributeError:
            return default


class DevelopmentConfig(Config):
    """开发环境配置。"""
    DEBUG: bool = True
    FLASK_ENV: str = "development"


class ProductionConfig(Config):
    """生产环境配置。"""
    DEBUG: bool = False
    FLASK_ENV: str = "production"


def get_config() -> Config:
    """根据当前环境返回对应的配置类实例。"""
    env: str = os.getenv("FLASK_ENV", "development")
    if env == "production":
        return ProductionConfig()
    return DevelopmentConfig()
