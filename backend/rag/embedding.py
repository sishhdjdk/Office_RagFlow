# rag/embedding.py
import torch
from sentence_transformers import SentenceTransformer
import numpy as np
import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
class EmbeddingModel:
    _model = None

    @classmethod
    def load(cls, model_name: str = "BAAI/bge-small-zh-v1.5"):
        """首次调用时下载模型（约 100MB），存在本地缓存"""
        if cls._model is not None:
            return cls
        device ="cuda" if torch.cuda.is_available() else "cpu"
        cls._model=SentenceTransformer(model_name, device=device)
        print(f"EmbeddingModel 加载设备 {device}")
        return cls

    @classmethod
    def encode(cls, texts: list[str]) -> np.ndarray:
        """批量编码文本 → (N, 512) 向量"""
        if cls._model is None:
            raise RuntimeError("EmbeddingModel 未加载，请先调用 load()")
        embeddings = cls._model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)
        return embeddings

    @classmethod
    def encode_query(cls, text: str) -> np.ndarray:
        """编码查询文本 → (512,) 向量"""
        if cls._model is None:
            raise RuntimeError("EmbeddingModel 未加载，请先调用 load()")
        embedding = cls._model.encode(text, normalize_embeddings=True, convert_to_numpy=True)
        return embedding