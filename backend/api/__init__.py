"""API 应用工厂。

这里负责注册认证、知识库、文件、文档等核心蓝图，并在启动时完成基础数据初始化。
"""

from flask import Flask, jsonify
from flask_cors import CORS
from api.settings import Settings
from api.db.db_models import db


def create_app():
    # API 侧应用工厂：负责初始化配置、基础扩展和业务蓝图。
    app = Flask(__name__)
    app.config.from_object(Settings)

    # 只放行前端开发地址，便于本地联调。
    CORS(app, origins=["http://localhost:3000"], supports_credentials=True)

    # 数据库扩展在这里绑定到应用上下文。
    db.init_app(app)

    with app.app_context():
        # 启动时建表并补默认数据，避免首次运行还要手工初始化。
        db.create_all()
        _seed_default_data()

    # 业务路由集中注册，入口关系清晰。
    _register_blueprints(app)
    _register_system_routes(app)

    return app


def _register_blueprints(app):
    # 认证、数据集、文件、文档是知识库主链路的四个核心蓝图。
    from api.apps import auth_bp
    from api.apps.restful_apis.dataset_api import dataset_bp
    from api.apps.restful_apis.file_api import file_bp
    from api.apps.restful_apis.document_api import document_bp

    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(dataset_bp, url_prefix="/api/v1")
    app.register_blueprint(file_bp, url_prefix="/api/v1")
    app.register_blueprint(document_bp, url_prefix="/api/v1")


def _register_system_routes(app):
    """系统级路由（健康检查等）"""

    @app.route("/api/v1/system/health")
    def health_check():
        # 运维探活接口：逐项确认后端依赖是否正常。
        checks = {}

        # 数据库检查。
        try:
            from sqlalchemy import text
            db.session.execute(text("SELECT 1"))
            checks["mysql"] = "ok"
        except Exception as e:
            checks["mysql"] = f"error: {e}"

        # 缓存检查。
        try:
            import redis
            r = redis.from_url(Settings.REDIS_URL)
            r.ping()
            checks["redis"] = "ok"
        except Exception as e:
            checks["redis"] = f"error: {e}"

        # 对象存储检查，缺桶时自动创建，降低首次部署门槛。
        try:
            from minio import Minio
            client = Minio(
                Settings.MINIO_ENDPOINT,
                access_key=Settings.MINIO_ACCESS_KEY,
                secret_key=Settings.MINIO_SECRET_KEY,
                secure=False,
            )
            if not client.bucket_exists(Settings.MINIO_BUCKET):
                client.make_bucket(Settings.MINIO_BUCKET)
            checks["minio"] = "ok"
        except Exception as e:
            checks["minio"] = f"error: {e}"

        # 向量服务通过 HTTP 直连探测，仅影响健康状态展示。
        try:
            import requests
            resp = requests.get(
                f"http://{Settings.INFINITY_HOST}:{Settings.INFINITY_PORT}/admin/node/status",
                timeout=3
            )
            checks["infinity"] = "ok" if resp.status_code == 200 else f"error: HTTP {resp.status_code}"
        except Exception as e:
            checks["infinity"] = f"skipped: {str(e)[:80]}"

        # 主流程依赖数据库、缓存和对象存储，Infinity 允许降级。
        required_checks = {k: v for k, v in checks.items() if k != "infinity"}
        all_ok = all(v == "ok" for v in required_checks.values())
        return jsonify({
            "status": "healthy" if all_ok else "degraded",
            "version": "0.1.0",
            "checks": checks,
        }), 200 if all_ok else 503


def _seed_default_data():
    """首次运行时创建默认租户和超级管理员"""
    from api.db.db_models import Tenant, User

    if Tenant.query.first() is None:
        # 只在空库场景注入默认租户和管理员，避免覆盖已有数据。
        tenant = Tenant(name="默认租户", code="default")
        db.session.add(tenant)
        db.session.flush()

        admin = User(
            tenant_id=tenant.id,
            username="admin",
            password_hash=User.hash_password("admin123"),
            real_name="系统管理员",
            role="super_admin",
            security_level=4,
            is_active=True,
        )
        db.session.add(admin)
        db.session.commit()
