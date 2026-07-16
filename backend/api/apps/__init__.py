"""认证与请求上下文入口。

这里负责把 JWT 解析结果转换成 Flask g 上下文，再供数据集、文件、文档接口复用。
"""

import functools
import jwt
from datetime import datetime, timedelta, timezone
from flask import Blueprint, request, g

from api.db.db_models import User, db
from api.utils.jwt_utils import decode_token, create_access_token, create_refresh_token
from api.utils.response import success, error


auth_bp = Blueprint("auth", __name__)


# ==================== 鉴权装饰器 ====================

class AuthError(Exception):
    def __init__(self, message: str, status_code: int = 401):
        # 统一携带错误文案和状态码，供认证链路直接抛出。
        self.message = message
        self.status_code = status_code


def login_required(f):
    """全局接口鉴权装饰器（对标 RAGFlow login_required）"""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        # Token 可以来自请求头或 query 参数，方便前端和调试工具调用。
        token = _extract_token()
        if not token:
            return error("缺少认证令牌", 401)

        try:
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            return error("令牌已过期，请重新登录", 401)
        except jwt.InvalidTokenError:
            return error("无效的认证令牌", 401)

        # 访问业务接口必须使用 Access Token，Refresh Token 只用于续期。
        if payload.get("type") == "refresh":
            return error("请使用 Access Token 而非 Refresh Token", 401)

        user = User.query.get(payload["sub"])
        if not user or not user.is_active:
            return error("用户不存在或已被禁用", 401)

        # 把用户上下文写入 g，后续业务路由直接复用。
        g.current_user = user
        g.tenant_id = user.tenant_id
        g.security_level = user.security_level
        g.role = user.role
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """管理员接口鉴权装饰器"""
    @functools.wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if g.role not in ("super_admin", "admin"):
            return error("需要管理员权限", 403)
        return f(*args, **kwargs)
    return decorated


def _extract_token():
    # 优先读 Authorization Bearer，其次兼容 query 参数 token。
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return request.args.get("token")


# ==================== 认证路由 ====================

@auth_bp.route("/login", methods=["POST"])
def login():
    """用户名 + 密码登录"""
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return error("用户名和密码不能为空")

    user = User.query.filter_by(username=username).first()
    if not user:
        return error("用户名或密码错误", 401)

    if not user.is_active:
        return error("账户已被禁用", 403)

    # 连续失败会触发短时锁定，减少暴力尝试风险。
    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        return error("账户已被锁定，请稍后再试", 423)

    if not user.verify_password(password):
        user.login_failed_count = (user.login_failed_count or 0) + 1
        if user.login_failed_count >= 5:
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)
        db.session.commit()
        return error("用户名或密码错误", 401)

    user.login_failed_count = 0
    user.locked_until = None
    user.last_login_at = datetime.now(timezone.utc)
    db.session.commit()

    # 登录成功后同时签发短期访问令牌和长期刷新令牌。
    access_token = create_access_token(
        user_id=user.id,
        tenant_id=user.tenant_id,
        role=user.role,
        security_level=user.security_level,
    )
    refresh_token = create_refresh_token(user_id=user.id)

    return success({
        "token": access_token,
        "refresh_token": refresh_token,
        "user": user.to_dict(),
    })


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    """登出"""
    return success(None, "已登出")


@auth_bp.route("/me", methods=["GET"])
@login_required
def get_current_user():
    """获取当前登录用户信息"""
    # 前端用它恢复会话和初始化用户态。
    return success(g.current_user.to_dict())
