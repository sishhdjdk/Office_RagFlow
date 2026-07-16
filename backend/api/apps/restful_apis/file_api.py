"""文件接口。

这里管理的是最原始的上传文件记录，不直接关心知识库归属，只负责对象存储与数据库元数据同步。
"""

from flask import Blueprint, request, g
from werkzeug.utils import secure_filename

from api.apps import login_required
from api.db.db_models import db, File
from api.utils.s3_client import upload_file, remove_object
from api.utils.response import success, error, paginated


file_bp = Blueprint("file", __name__)


@file_bp.route("/files", methods=["GET"])
@login_required
def list_files():
    # 只列当前租户上传过的原始文件，文件是文档的上游入口。
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 20, type=int)

    query = File.query.filter_by(tenant_id=g.tenant_id)
    total = query.count()
    items = query.order_by(File.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return paginated([f.to_dict() for f in items], total, page, page_size)


@file_bp.route("/files/upload", methods=["POST"])
@login_required
def upload_file_endpoint():
    # 上传文件先落对象存储，再写数据库记录，保证 file 表和存储内容一致。
    if "file" not in request.files:
        return error("请选择要上传的文件")

    file_obj = request.files["file"]
    if not file_obj.filename:
        return error("文件名为空")

    original_name = secure_filename(file_obj.filename)
    content_type = file_obj.content_type or "application/octet-stream"

    # 返回 object_key 和文件大小，供后续文档创建时复用。
    result = upload_file(file_obj, original_name, content_type)

    db_file = File(
        tenant_id=g.tenant_id,
        user_id=g.current_user.id,
        original_name=original_name,
        object_key=result["object_key"],
        file_size=result["file_size"],
        mime_type=content_type,
    )
    db.session.add(db_file)
    db.session.commit()

    return success(db_file.to_dict())


@file_bp.route("/files/<file_id>", methods=["GET"])
@login_required
def get_file(file_id):
    db_file = File.query.filter_by(id=file_id, tenant_id=g.tenant_id).first()
    if not db_file:
        return error("文件不存在", 404)
    return success(db_file.to_dict())


@file_bp.route("/files/<file_id>", methods=["DELETE"])
@login_required
def delete_file(file_id):
    # 先删对象存储，再删数据库记录，避免留下悬挂的元数据。
    db_file = File.query.filter_by(id=file_id, tenant_id=g.tenant_id).first()
    if not db_file:
        return error("文件不存在", 404)
    remove_object(db_file.object_key, db_file.bucket_name)
    db.session.delete(db_file)
    db.session.commit()
    return success(None, "已删除")
