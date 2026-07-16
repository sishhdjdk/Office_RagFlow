"""应用主入口。

这里负责创建 Flask 实例、挂载全局错误处理和健康检查，不承载具体业务路由。
"""

import logging
import os
from typing import Any

from flask import Flask, jsonify
from flask_cors import CORS

from config import get_config

# 健康检查只需要在请求时验证依赖，不把这些库变成应用启动强依赖。
try:
    from sqlalchemy import Engine, create_engine, text
    from redis import Redis
    from minio import Minio
    import requests
    _OPTIONAL_DEPS_AVAILABLE = True
except ImportError:
    _OPTIONAL_DEPS_AVAILABLE = False

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("govrag")


def create_app() -> Flask:
    """创建 Flask 应用实例（工厂模式）。"""
    app = Flask(__name__)
    config = get_config()
    app.config.from_object(config)

    # 前后端分离场景下，接口只放行配置里的前端来源。
    cors_origins: list[str] = [app.config.get("CORS_ORIGINS", "http://localhost:3000")]
    CORS(app, origins=cors_origins, supports_credentials=True)

    # 统一错误出口，避免各路由重复拼错误响应。
    _register_error_handlers(app)

    # 业务蓝图在这里集中挂载，路由结构一眼可见。
    _register_blueprints(app)

    logger.info("Flask 应用已创建，环境: %s", config.get("FLASK_ENV", "development"))
    return app


def _register_error_handlers(app: Flask) -> None:
    """注册全局错误处理器。"""

    @app.errorhandler(400)
    def bad_request(error: Any) -> tuple:
        return jsonify({"error": "请求参数错误", "detail": str(error)}), 400

    @app.errorhandler(401)
    def unauthorized(error: Any) -> tuple:
        return jsonify({"error": "未授权访问"}), 401

    @app.errorhandler(404)
    def not_found(error: Any) -> tuple:
        return jsonify({"error": "资源不存在"}), 404

    @app.errorhandler(500)
    def internal_error(error: Any) -> tuple:
        logger.exception("服务器内部错误: %s", error)
        return jsonify({"error": "服务器内部错误"}), 500


def _register_blueprints(app: Flask) -> None:
    """注册所有 Flask Blueprint 路由。"""
    # 健康检查：用于运维探活，按依赖逐项验证数据库、缓存、对象存储和向量服务。
    @app.route("/api/v1/system/health")
    def health_check() -> tuple:
        """验证 MySQL、Redis、MinIO、Infinity 连通性。"""
        if not _OPTIONAL_DEPS_AVAILABLE:
            return jsonify({
                "status": "degraded",
                "version": "0.1.0",
                "message": "部分依赖未安装，无法执行完整健康检查",
            }), 503

        checks: dict[str, str] = {}

        # 1. 数据库可用性检查。
        try:
            engine: Engine = create_engine(app.config["SQLALCHEMY_DATABASE_URI"])
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            checks["mysql"] = "ok"
        except Exception as e:
            logger.warning("MySQL 健康检查失败: %s", e)
            checks["mysql"] = f"error: {e}"

        # 2. Redis 可用性检查。
        try:
            r: Redis = Redis.from_url(app.config["REDIS_URL"])
            r.ping()
            checks["redis"] = "ok"
        except Exception as e:
            logger.warning("Redis 健康检查失败: %s", e)
            checks["redis"] = f"error: {e}"

        # 3. 对象存储可用性检查，必要时顺手补齐默认桶。
        try:
            endpoint: str = app.config["MINIO_ENDPOINT"]
            client = Minio(
                endpoint,
                access_key=app.config["MINIO_ACCESS_KEY"],
                secret_key=app.config["MINIO_SECRET_KEY"],
                secure=False,
            )
            bucket: str = app.config["MINIO_BUCKET"]
            if not client.bucket_exists(bucket):
                client.make_bucket(bucket)
                logger.info("MinIO 存储桶 '%s' 已自动创建", bucket)
            checks["minio"] = "ok"
        except Exception as e:
            logger.warning("MinIO 健康检查失败: %s", e)
            checks["minio"] = f"error: {e}"

        # 4. 向量库检查是辅助项，不影响主链路时可降级返回。
        try:
            infinity_url: str = (
                f"http://{app.config['INFINITY_HOST']}:{app.config['INFINITY_PORT']}"
                "/admin/node/status"
            )
            resp = requests.get(infinity_url, timeout=3)
            checks["infinity"] = "ok" if resp.status_code == 200 else f"error: HTTP {resp.status_code}"
        except Exception as e:
            checks["infinity"] = f"skipped: {str(e)[:80]}"

        # 主链路依赖三项都正常才算 healthy，Infinity 只参与可观测性。
        required_checks: dict[str, str] = {k: v for k, v in checks.items() if k != "infinity"}
        all_ok: bool = all(v == "ok" for v in required_checks.values())
        status: str = "healthy" if all_ok else "degraded"

        logger.info("健康检查完成: status=%s, checks=%s", status, checks)
        return jsonify({
            "status": status,
            "version": "0.1.0",
            "checks": checks,
        }), 200 if all_ok else 503


if __name__ == "__main__":
    app = create_app()
    host: str = os.getenv("FLASK_HOST", "0.0.0.0")
    port: int = int(os.getenv("FLASK_PORT", "5000"))
    debug: bool = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    logger.info("启动 Flask 开发服务器: %s:%s (debug=%s)", host, port, debug)
    app.run(host=host, port=port, debug=debug)
