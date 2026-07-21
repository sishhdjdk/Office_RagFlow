from flask import Blueprint, request, g
from api.apps import login_required
from api.db.db_models import Document, Chunk
from api.utils.response import success, error, paginated


chunk_bp = Blueprint("chunk", __name__)


@chunk_bp.route("/documents/<doc_id>/chunks", methods=["GET"])
@login_required
def list_chunks(doc_id):
    doc = Document.query.filter_by(id=doc_id, tenant_id=g.tenant_id).first()
    if not doc:
        return error("文档不存在", 404)

    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 50, type=int)

    query = Chunk.query.filter_by(document_id=doc_id, tenant_id=g.tenant_id)
    total = query.count()
    items = query.order_by(Chunk.chunk_index.asc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return paginated([c.to_dict() for c in items], total, page, page_size)


@chunk_bp.route("/chunks/<chunk_id>", methods=["GET"])
@login_required
def get_chunk(chunk_id):
    chunk = Chunk.query.filter_by(id=chunk_id, tenant_id=g.tenant_id).first()
    if not chunk:
        return error("切片不存在", 404)
    return success(chunk.to_dict())
