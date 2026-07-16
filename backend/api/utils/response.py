"""统一 API 响应封装。

所有核心接口尽量返回同一套 code / message / data 结构，前端只需按这个约定解析即可。
"""

from flask import jsonify
from typing import Any


def success(data: Any = None, message: str = "ok") -> tuple:
    # 成功响应统一使用 code=0，便于前端做通用判断。
    return jsonify({"code": 0, "message": message, "data": data}), 200


def paginated(items: list, total: int, page: int, page_size: int) -> tuple:
    # 分页响应固定返回 items + total + page 信息，避免各接口自行拼结构。
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
    # 失败响应只返回统一错误码和消息，不额外混入业务 payload。
    return jsonify({"code": -1, "message": message}), code
