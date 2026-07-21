# api/utils/vector_store.py

import numpy as np
import os
import faiss

class VectorStore:
    def __init__(self, index_dir: str, dim: int = 512):
        """index_dir: FAISS 索引文件目录"""
        self.index_dir=index_dir
        self.dim=dim #role: 向量维度
        self.index_path=os.path.join(index_dir, "index.faiss") #role: FAISS 索引文件路径
        self.id_path=os.path.join(index_dir, "id_list.npy") #role: chunk_id 映射文件路径
        os.makedirs(index_dir, exist_ok=True)
        
        if os.path.exists(self.index_path):
            self.index=faiss.read_index(self.index_path)#role: 读取 FAISS 索引
            self._id_list=np.load(self.id_path).tolist()#role: 读取 chunk_id 映射
        else:
            self.index=faiss.IndexFlatL2(dim)#role: 创建 FAISS 索引
            self._id_list=[]#role: 初始化 chunk_id 映射

    def add(self, vectors: np.ndarray, chunk_ids: list[str]):
        """写入向量，需维护 chunk_id → FAISS 内部 ID 的映射"""
        self.index.add(np.ascontiguousarray(vectors, dtype=np.float32))#role: 添加向量到 FAISS 索引
        self._id_list.extend(chunk_ids)

    def search(self, query_vec: np.ndarray, top_k: int = 10) -> list[tuple[str, float]]:
        """返回 [(chunk_id, distance), ...]，按距离升序"""
        query = np.array([query_vec], dtype=np.float32)#role: 将查询向量转换为二维数组
        distances, indices = self.index.search(query, top_k)#role: 在 FAISS 索引中搜索最接近的 top_k 个向量
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:           # FAISS 用 -1 表示无效
                continue
            results.append((self._id_list[idx], float(dist)))
        return results

    def save(self):
        """持久化到磁盘"""
        faiss.write_index(self.index, self.index_path)#role: 保存 FAISS 索引到磁盘
        np.save(self.id_path, np.array(self._id_list))#role: 保存 chunk_id 映射到磁盘
        
    #role: 返回索引中向量的数量
    def count(self) -> int:
        return self.index.ntotal