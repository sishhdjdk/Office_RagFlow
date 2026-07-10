# rag_backend/app.py
from flask import Flask, jsonify
from flask_cors import CORS

from config import get_config


def create_app():
    app = Flask(__name__)
    config = get_config()
    app.config.from_object(config)

    CORS(app, origins=["http://localhost:3000"], supports_credentials=True)

    # ========== 健康检查（你最需要的第一个接口）==========
    @app.route("/api/v1/system/health")
    def health_check():
        """验证 4 个中间件连通性"""
        checks = {}

        # 1. MySQL
        try:
            from sqlalchemy import create_engine, text
            engine = create_engine(app.config["SQLALCHEMY_DATABASE_URI"])
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            checks["mysql"] = "ok"
        except Exception as e:
            checks["mysql"] = f"error: {e}"

        # 2. Redis
        try:
            import redis
            r = redis.from_url(app.config["REDIS_URL"])
            r.ping()
            checks["redis"] = "ok"
        except Exception as e:
            checks["redis"] = f"error: {e}"

        # 3. MinIO
        try:
            from minio import Minio
            endpoint = app.config["MINIO_ENDPOINT"]
            client = Minio(
                endpoint,
                access_key=app.config["MINIO_ACCESS_KEY"],
                secret_key=app.config["MINIO_SECRET_KEY"],
                secure=False,
            )
            # 确保 bucket 存在
            bucket = app.config["MINIO_BUCKET"]
            if not client.bucket_exists(bucket):
                client.make_bucket(bucket)
            checks["minio"] = "ok"
        except Exception as e:
            checks["minio"] = f"error: {e}"

        # 4. Infinity（HTTP 直连，绕过 SDK C++ 层）
        try:
            import requests
            resp = requests.get(
                f"http://{app.config['INFINITY_HOST']}:{app.config['INFINITY_PORT']}/admin/node/status",
                timeout=3
            )
            checks["infinity"] = "ok" if resp.status_code == 200 else f"error: HTTP {resp.status_code}"
        except Exception as e:
            checks["infinity"] = f"skipped: {str(e)[:80]}"

        required_checks = {k: v for k, v in checks.items() if k != "infinity"}
        all_ok = all(v == "ok" for v in required_checks.values())
        return jsonify({
            "status": "healthy" if all_ok else "degraded",
            "version": "0.1.0",
            "checks": checks,
        }), 200 if all_ok else 503

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)