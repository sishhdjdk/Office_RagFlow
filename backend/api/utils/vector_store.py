# api/utils/vector_store.py

import numpy as np
import os
import faiss

class VectorStore:
    def __init__(self, index_dir: str, dim: int = 512):
        """index_dir: FAISS 索引文件目录"""
        self.index_dir = os.path.abspath(index_dir)
        self.dim = dim
        self.index_path = os.path.join(self.index_dir, "index.faiss")
        self.id_path = os.path.join(self.index_dir, "id_list.npy")
        os.makedirs(self.index_dir, exist_ok=True)

        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
            self._id_list = np.load(self.id_path).tolist()
            print(f"[VectorStore] 加载已有索引 {self.index_path}, ntotal={self.index.ntotal}")
        else:
            self.index = faiss.IndexFlatL2(dim)
            self._id_list = []
            print(f"[VectorStore] 创建新空索引 {self.index_path}")

    def add(self, vectors: np.ndarray, chunk_ids: list[str]):
        """写入向量，需维护 chunk_id → FAISS 内部 ID 的映射"""
        self.index.add(np.ascontiguousarray(vectors, dtype=np.float32))#role: 添加向量到 FAISS 索引
        self._id_list.extend(chunk_ids)

    def search(self, query_vec: np.ndarray, top_k: int = 10) -> list[tuple[str, float]]:
        """返回 [(chunk_id, distance), ...]，按距离升序"""
        print(f"[VectorStore] 索引含 {self.index.ntotal} 个向量, id_list 长度 {len(self._id_list)}")
        query = np.array([query_vec], dtype=np.float32)
        distances, indices = self.index.search(query, top_k)
        print(f"[VectorStore] search 返回 distances={distances[0][:3]}, indices={indices[0][:3]}")
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
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