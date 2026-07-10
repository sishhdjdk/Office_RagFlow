# rag_backend/config.py
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """基础配置"""
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")

    # MySQL
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "123456")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "office_ragflow")
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        "?charset=utf8mb4"
    )

    # Redis
    REDIS_URL = os.getenv("REDIS_URL", "redis://:redis123@localhost:6379/0")

    # MinIO
    MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    MINIO_BUCKET = os.getenv("MINIO_BUCKET", "govrag")

    # Infinity 向量库
    INFINITY_HOST = os.getenv("INFINITY_HOST", "localhost")
    INFINITY_PORT = int(os.getenv("INFINITY_PORT", "23817"))

    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret")
    JWT_ALGORITHM = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 120


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


def get_config():
    env = os.getenv("FLASK_ENV", "development")
    if env == "production":
        return ProductionConfig()
    return DevelopmentConfig()