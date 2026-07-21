from flask import Blueprint, request, g
from api.apps import login_required
from api.utils.response import success, error, paginated
from rag.embedding import EmbeddingModel
from api.utils.vector_store import VectorStore
from api.db.db_models import Chunk


search_bp = Blueprint("search", __name__)

@search_bp.route("/search", methods=["POST"])
@login_required
def search():
    data=request.get_json(silent=True) or {}
    question=data.get("question")
    kb_ids=data.get("kb_ids", [])#解释：知识库ID列表
    top_k=data.get("top_k", 5)#解释：返回结果数量
    EmbeddingModel.load()
    query_vec=EmbeddingModel.encode_query(question)
    
    all_results = []
    
    #一个 kb_ids 可能对应多个 FAISS 索引
    for kb_id in kb_ids:
        vs=VectorStore(f"data/faiss/{kb_id}")
        results=vs.search(query_vec, top_k)
        all_results.extend(results)
    
    #合并后按举例升序取top_k
    all_results.sort(key=lambda x: x[1])#按相似度升序排列
    all_results=all_results[:top_k]#取前top_k个结果
    
    #查询对应的切片内容
    chunk_ids = [cid for cid, _ in all_results]
    chunks = Chunk.query.filter(Chunk.id.in_(chunk_ids)).all()

    # 组装最终结果
    response = []
    for cid, score in all_results:
        chunk = next((c for c in chunks if str(c.id) == cid), None)
        if chunk:
            response.append({
                "chunk_id": cid,
                "content": chunk.content,
                "score": float(score),
                "document_id": str(chunk.document_id),
            })

    return success(response)