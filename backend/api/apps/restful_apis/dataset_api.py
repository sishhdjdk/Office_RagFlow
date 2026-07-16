"""数据集接口。

负责知识库容器的增删改查，以及返回文档数量等汇总信息。
"""

from flask import Blueprint, request, g
from api.apps import login_required
from api.db.db_models import db, Dataset, Document
from api.utils.response import success, error, paginated


dataset_bp = Blueprint("dataset", __name__)


@dataset_bp.route("/datasets", methods=["GET"])
@login_required
def list_datasets():
    # 列表只看当前租户的数据集，并补上文档数，方便前端直接展示概览。
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 20, type=int)

    query = Dataset.query.filter_by(tenant_id=g.tenant_id)
    total = query.count()
    items = query.order_by(Dataset.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    result = []
    for d in items:
        item = d.to_dict()
        item["document_count"] = Document.query.filter_by(
            dataset_id=d.id, tenant_id=g.tenant_id
        ).count()
        result.append(item)

    return paginated(result, total, page, page_size)


@dataset_bp.route("/datasets", methods=["POST"])
@login_required
def create_dataset():
    # 新建数据集时把向量模型和切分参数一起保存，后续导入文档会直接复用。
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    if not name:
        return error("数据集名称不能为空")

    embedding_model = data.get("embedding_model", "bge-large-zh-v1.5")
    existed = Dataset.query.filter_by(tenant_id=g.tenant_id, name=name).first()
    if existed:
        return error("数据集名称已存在")

    dataset = Dataset(
        tenant_id=g.tenant_id,
        name=name,
        description=data.get("description", ""),
        embedding_model=embedding_model,
        chunk_size=data.get("chunk_size", 512),
        chunk_overlap=data.get("chunk_overlap", 50),
        parser_config=data.get("parser_config", {}),
        security_level=data.get("security_level", 0),
        created_by=g.current_user.id,
    )
    db.session.add(dataset)
    db.session.commit()

    return success(dataset.to_dict())


@dataset_bp.route("/datasets/<dataset_id>", methods=["GET"])
@login_required
def get_dataset(dataset_id):
    dataset = Dataset.query.filter_by(id=dataset_id, tenant_id=g.tenant_id).first()
    if not dataset:
        return error("数据集不存在", 404)
    return success(dataset.to_dict())


@dataset_bp.route("/datasets/<dataset_id>", methods=["PUT"])
@login_required
def update_dataset(dataset_id):
    # 更新只允许修改数据集元配置，不在这里直接碰文档内容。
    dataset = Dataset.query.filter_by(id=dataset_id, tenant_id=g.tenant_id).first()
    if not dataset:
        return error("数据集不存在", 404)

    data = request.get_json(silent=True) or {}
    for field in ("name", "description", "embedding_model", "chunk_size",
                  "chunk_overlap", "security_level"):
        if field in data:
            setattr(dataset, field, data[field])

    db.session.commit()
    return success(dataset.to_dict())


@dataset_bp.route("/datasets/<dataset_id>", methods=["DELETE"])
@login_required
def delete_dataset(dataset_id):
    dataset = Dataset.query.filter_by(id=dataset_id, tenant_id=g.tenant_id).first()
    if not dataset:
        return error("数据集不存在", 404)
    db.session.delete(dataset)
    db.session.commit()
    return success(None, "已删除")
