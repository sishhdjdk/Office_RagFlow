"""文档接口。

文档是数据集里的业务内容单元，通常由已上传文件创建并补充元数据。
"""

from flask import Blueprint, request, g
from api.apps import login_required
from api.db.db_models import db, Document, Dataset, File
from api.utils.response import success, error, paginated


document_bp = Blueprint("document", __name__)


@document_bp.route("/datasets/<dataset_id>/documents", methods=["GET"])
@login_required
def list_documents(dataset_id):
    # 文档列表必须先确认数据集归属，避免跨租户读取。
    dataset = Dataset.query.filter_by(id=dataset_id, tenant_id=g.tenant_id).first()
    if not dataset:
        return error("数据集不存在", 404)

    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 20, type=int)

    query = Document.query.filter_by(dataset_id=dataset_id, tenant_id=g.tenant_id)
    total = query.count()
    items = query.order_by(Document.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return paginated([d.to_dict() for d in items], total, page, page_size)


@document_bp.route("/datasets/<dataset_id>/documents", methods=["POST"])
@login_required
def create_document(dataset_id):
    """创建文档（关联已上传的文件）"""
    # 这里的 file_ids 表示“已上传但尚未纳入知识库”的文件记录。
    dataset = Dataset.query.filter_by(id=dataset_id, tenant_id=g.tenant_id).first()
    if not dataset:
        return error("数据集不存在", 404)

    data = request.get_json(silent=True) or {}
    file_ids = data.get("file_ids", [])

    if not file_ids:
        return error("请提供 file_ids（已上传文件的 ID 列表）")

    files = File.query.filter(
        File.id.in_(file_ids),
        File.tenant_id == g.tenant_id,
    ).all()

    if len(files) != len(file_ids):
        return error("部分文件不存在或无权访问")

    docs = []
    # 一个文件生成一条文档记录，后续解析、切块、向量化都围绕文档展开。
    for f in files:
        doc = Document(
            tenant_id=g.tenant_id,
            dataset_id=dataset_id,
            name=data.get("name") or f.original_name,
            file_type=f.mime_type,
            file_size=f.file_size,
            file_path=f.object_key,
            security_level=data.get("security_level", 0),
            doc_type=data.get("doc_type", ""),
            doc_year=data.get("doc_year", ""),
            issuing_org=data.get("issuing_org", ""),
            doc_number=data.get("doc_number", ""),
            topic_words=data.get("topic_words", ""),
            uploaded_by=g.current_user.id,
        )
        db.session.add(doc)
        docs.append(doc)

    # 先 flush 让新增文档进入当前事务，再回写数据集统计字段。
    db.session.flush()
    dataset.document_count = Document.query.filter_by(
        dataset_id=dataset_id, tenant_id=g.tenant_id
    ).count()

    db.session.commit()
    return success([d.to_dict() for d in docs])


@document_bp.route("/documents/<doc_id>", methods=["GET"])
@login_required
def get_document(doc_id):
    doc = Document.query.filter_by(id=doc_id, tenant_id=g.tenant_id).first()
    if not doc:
        return error("文档不存在", 404)
    return success(doc.to_dict())


@document_bp.route("/documents/<doc_id>", methods=["DELETE"])
@login_required
def delete_document(doc_id):
    # 删除文档后同步刷新数据集文档数，避免前端概览失真。
    doc = Document.query.filter_by(id=doc_id, tenant_id=g.tenant_id).first()
    if not doc:
        return error("文档不存在", 404)

    dataset_id = doc.dataset_id
    db.session.delete(doc)
    db.session.flush()

    dataset = Dataset.query.filter_by(id=dataset_id, tenant_id=g.tenant_id).first()
    if dataset:
        dataset.document_count = Document.query.filter_by(
            dataset_id=dataset_id, tenant_id=g.tenant_id
        ).count()

    db.session.commit()
    return success(None, "已删除")
