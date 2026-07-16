"""JWT 签发与解析工具。

Access Token 承载当前访问权限，Refresh Token 仅用于续期，不直接访问业务接口。
"""

import jwt
import uuid
from datetime import datetime, timedelta, timezone
from api.settings import Settings


def create_access_token(user_id, tenant_id, role, security_level, expires_minutes=None):
    """签发 JWT Access Token"""
    if expires_minutes is None:
        expires_minutes = Settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES

    now = datetime.now(timezone.utc)
    # Access Token 携带当前请求所需的租户、角色和安全级别信息。
    payload = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "role": role,
        "security_level": security_level,
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
        "jti": str(uuid.uuid4()),
    }
    token = jwt.encode(payload, Settings.JWT_SECRET_KEY, algorithm=Settings.JWT_ALGORITHM)
    return token


def create_refresh_token(user_id):
    """签发 Refresh Token"""
    now = datetime.now(timezone.utc)
    # Refresh Token 只保留身份和类型标记，不携带业务权限信息。
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(days=Settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
        "jti": str(uuid.uuid4()),
    }
    token = jwt.encode(payload, Settings.JWT_SECRET_KEY, algorithm=Settings.JWT_ALGORITHM)
    return token


def decode_token(token):
    """校验并解码 JWT Token"""
    # 解码和验签统一走这里，供鉴权装饰器复用。
    return jwt.decode(token, Settings.JWT_SECRET_KEY, algorithms=[Settings.JWT_ALGORITHM])
