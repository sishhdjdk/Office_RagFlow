from flask import Blueprint, request, g, Response, stream_with_context
from api.apps import login_required
from api.utils.response import success, error, paginated
from api.db.db_models import db, Dialog, Conversation, Dataset, TenantLLM
import json


chat_bp=Blueprint("chat", __name__)

#创建对话
@chat_bp.route("/chats", methods=["POST"])
@login_required 
def create_chat():  
    data=request.get_json(silent=True) or {}
    kb_ids=data.get("kb_ids")
    if not kb_ids:
        return error("至少选择一个知识库")
    #校验知识库
    datasets=Dataset.query.filter(Dataset.id.in_(kb_ids), Dataset.tenant_id==g.tenant_id).all()
    if len(datasets)!=len(kb_ids):
        return error("部分知识库不存在或不属于当前租户")

    default_llm = TenantLLM.query.filter_by(tenant_id=g.tenant_id, model_type="chat").first()
    default_rerank = TenantLLM.query.filter_by(tenant_id=g.tenant_id, model_type="rerank").first()

    dialog=Dialog(
        name=data.get("name"),
        tenant_id=g.tenant_id,
        user_id=g.current_user.id,
        kb_ids=kb_ids,
        llm_id=str(default_llm.id) if default_llm else "",
        rerank_id=str(default_rerank.id) if default_rerank else "",
    )
    db.session.add(dialog)
    db.session.commit()#提交事务
    return success(dialog.to_dict())
        

#对话列表
@chat_bp.route("/chats", methods=["GET"])
@login_required
def list_chats():
     # 列表只看当前租户的数据集，并补上文档数，方便前端直接展示概览。
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 20, type=int)

    query = Dialog.query.filter_by(tenant_id=g.tenant_id)
    total = query.count()
    items = query.order_by(Dialog.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    result = []
    for d in items:
        item = d.to_dict()
        item["conversation_count"] = Conversation.query.filter_by(
            dialog_id=d.id, tenant_id=g.tenant_id
        ).count()
        result.append(item)

    return paginated(result, total, page, page_size)



#对话详情
@chat_bp.route("/chats/<id>", methods=["GET"])
@login_required
def get_chat(id):
    chat=Dialog.query.filter(Dialog.id==id, Dialog.tenant_id==g.tenant_id, Dialog.user_id==g.current_user.id).first()
    if not chat:
        return error("会话不存在或不属于当前用户")
    return success(chat.to_dict())

# 问答
@chat_bp.route("/chats/<chat_id>/ask", methods=["POST"])
@login_required
def ask(chat_id):
    """流式问答（SSE）"""
    dialog = Dialog.query.filter(
        Dialog.id == chat_id,
        Dialog.tenant_id == g.tenant_id,
    ).first()
    if not dialog:
        return error("会话不存在", 404)

    data = request.get_json(silent=True) or {}
    question = data.get("question", "").strip()
    if not question:
        return error("问题不能为空")

    kb_ids = dialog.kb_ids or []
    if not kb_ids:
        return error("该对话未关联知识库")

    system_prompt = (dialog.prompt_config or {}).get("system", "")

    from rag.nlp.search import Retriever
    from rag.llm.chat_model import ChatModel

    llm_config = TenantLLM.query.get(dialog.llm_id) if dialog.llm_id else None
    if llm_config and llm_config.api_key:
        model = ChatModel(
            api_base=llm_config.api_base or "",
            api_key=llm_config.api_key or "",
            model_name=llm_config.llm_name or "",
        )
    else:
        model = ChatModel()

    
    retriever = Retriever(chat_model=model)
    retrieved = retriever.retrieve(question, kb_ids) # 执行知识库检索，把匹配到的文档片段存入变量 retrieved

    # 生成参考文献列表
    references = [
        {"chunk_id": c["chunk_id"], "content_snippet": c["content"][:200], "score": c["score"]}
        for c in retrieved
    ]
    # 加载历史
    past=Conversation.query.filter_by(dialog_id=dialog.id, tenant_id=dialog.tenant_id).order_by(Conversation.created_at.asc()).limit(5).all()
    
    #构造messages
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    for conv_item in past:
        msg=conv_item.message#作用：获取历史对话的消息内容
        if isinstance(msg, dict):
            messages.append({"role": "user", "content": msg.get("question", "")})
            messages.append({"role": "assistant", "content": msg.get("answer", "")})

    # 拼接问题+上下文检索
    parts = [f"【参考资料{i+1}】\n{r['content']}" for i, r in enumerate(retrieved)]
    ctx = "\n\n---\n\n".join(parts)
    messages.append({"role": "user", "content": f"参考资料：\n{ctx}\n\n问题：{question}\n\n回答："})
    

    def generate():#解释：生成SSE流
        full_answer = ""
        for token in model.stream_chat(messages=messages):
            full_answer += token
            yield f"data: {json.dumps({'type': 'token', 'text': token})}\n\n"
            
        yield f"data: {json.dumps({'type': 'citations', 'citations': references})}\n\n"
        #保存conversion
        conv=Conversation(
            dialog_id=dialog.id,
            tenant_id=dialog.tenant_id,
            user_id=g.current_user.id,
            message={"question": question, "answer": full_answer},
            reference=references,
        )
        db.session.add(conv)
        db.session.commit()#提交事务
        yield f"data: {json.dumps({'type': 'citations', 'citations': references})}\n\n"
        yield "data: [DONE]\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
    
@chat_bp.route("/chats/<chat_id>/conversations", methods=["GET"])
@login_required
def list_conversations(chat_id):
    """获取对话的历史问答记录"""
    dialog = Dialog.query.filter(
        Dialog.id == chat_id,
        Dialog.tenant_id == g.tenant_id,
    ).first()
    if not dialog:
        return error("会话不存在", 404)

    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 50, type=int)

    query = Conversation.query.filter_by(dialog_id=dialog.id, tenant_id=dialog.tenant_id)
    total = query.count()
    items = query.order_by(Conversation.created_at.asc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    result = [item.to_dict() for item in items]
    return paginated(result, total, page, page_size)
