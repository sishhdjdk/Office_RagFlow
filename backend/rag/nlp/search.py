from rag.embedding import EmbeddingModel
from api.utils.vector_store import VectorStore
from api.db.db_models import Chunk
from rag.llm.chat_model import ChatModel
from typing import Optional

import os as _os
_DATA_DIR = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))), "data", "faiss")

class Retriever:
    def __init__(self, chat_model: Optional[ChatModel] = None):
        self.chat_model = chat_model or ChatModel()
    
    # 1. 检索
    def retrieve(self, question: str, kb_ids: list, top_k: int = 5):
        """检索 → 返回 top_k 个 chunk"""
        EmbeddingModel.load()
        query_vec=EmbeddingModel.encode_query(question)

        print(f"[Retriever] 查询: {question[:50]}, kb_ids: {kb_ids}")
        all_results = []
        
        #一个 kb_ids 可能对应多个 FAISS 索引
        for kb_id in kb_ids:
            vs=VectorStore(_os.path.join(_DATA_DIR, str(kb_id)))
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

        print(f"[Retriever] FAISS 命中 {len(all_results)} 条, MySQL 回查得到 {len(response)} 个文本")
        return response

    def ask(self,question:str,kb_ids:list,top_k:int=5,system_prompt:str="")-> str:
        """检索 + 问答 → 返回最终回答"""
        # 1. 检索
        retrieved_chunks=self.retrieve(question,kb_ids,top_k)
        # 2. 问答
        messages=self._build_messages(question,retrieved_chunks,system_prompt)
        answer=self.chat_model.chat(messages)
        #打印回答内容
        print(f"[Retriever] 问答完成，回答内容: {answer[:100]}...")
        return answer
    
    def ask_stream(self,question:str,kb_ids:list,top_k:int=5,system_prompt:str=""):
        """检索 + 问答 → 流式返回最终回答"""
        # 1. 检索
        retrieved_chunks=self.retrieve(question,kb_ids,top_k)
        full_answer = ""
        # 2. 问答
        messages=self._build_messages(question,retrieved_chunks,system_prompt)
        for token in self.chat_model.stream_chat(messages=messages):
            #打印输出
            full_answer += token
            yield token
        print(f"\n[Retriever] 流式问答完成，完整回答前100字符: {full_answer[:100]}...")

            
    def _build_messages(self,question, chunks, system_prompt):
        """构建消息列表"""
        context_parts = []
        for i,c in enumerate(chunks):
            context_parts.append(f"【参考资料{i+1}】\n{c['content']}")
        # 将检索到的 chunks 拼接成 context
        context = "\n\n---\n\n".join(context_parts)
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({
            "role": "user", 
            "content": f"请根据以下参考资料回答问题。\n\n参考资料：\n{context}\n\n问题：{question}\n\n回答："
        })
        return messages
