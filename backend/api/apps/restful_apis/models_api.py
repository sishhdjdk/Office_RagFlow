from flask import Blueprint, request, g
from api.apps import login_required, admin_required
from api.utils.response import success, error
from api.db.db_models import db, TenantLLM

models_bp = Blueprint("models", __name__)


@models_bp.route("/configs", methods=["GET"])
@login_required
def list_configs():
    configs = TenantLLM.query.filter_by(tenant_id=g.tenant_id).all()
    return success([c.to_dict() for c in configs])


@models_bp.route("/configs", methods=["POST"])
@login_required
def create_config():
    data = request.get_json(silent=True) or {}
    llm_name = data.get("llm_name", "").strip()
    model_type = data.get("model_type", "chat")
    api_key = data.get("api_key", "")
    api_base = data.get("api_base", "")

    if not llm_name:
        return error("模型名称不能为空", 400)

    config = TenantLLM(
        tenant_id=g.tenant_id,
        llm_name=llm_name,
        model_type=model_type,
        api_key=api_key,
        api_base=api_base,
    )
    db.session.add(config)
    db.session.commit()

    return success(config.to_dict())


@models_bp.route("/configs/<config_id>", methods=["PUT"])
@login_required
def update_config(config_id):
    config = TenantLLM.query.filter_by(id=config_id, tenant_id=g.tenant_id).first()
    if not config:
        return error("配置不存在", 404)

    data = request.get_json(silent=True) or {}
    if "llm_name" in data:
        config.llm_name = data["llm_name"].strip()
    if "model_type" in data:
        config.model_type = data["model_type"]
    if "api_key" in data:
        config.api_key = data["api_key"]
    if "api_base" in data:
        config.api_base = data["api_base"]

    db.session.commit()
    return success(config.to_dict())


@models_bp.route("/configs/<config_id>", methods=["DELETE"])
@login_required
def delete_config(config_id):
    config = TenantLLM.query.filter_by(id=config_id, tenant_id=g.tenant_id).first()
    if not config:
        return error("配置不存在", 404)

    db.session.delete(config)
    db.session.commit()
    return success(None, "已删除")
