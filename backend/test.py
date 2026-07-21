
# 测试1
# from deepdoc.parser.pdf_parser import PdfParser
# sections = PdfParser.parse("E:\\文件档案\\001-文献管理\\900-考研\\大学生数学竞赛习题辅导.pdf")
# print(f"共 {len(sections)} 页，第1页开头：{sections[1][0][:100]}")

#测试2
# from deepdoc.parser.pdf_parser import PdfParser
# from deepdoc.chunker.naive_chunker import naive_merge
# sections = PdfParser.parse("E:\\文件档案\\001-文献管理\\900-考研\\大学生数学竞赛习题辅导.pdf")
# chunks = naive_merge(sections, chunk_token_num=256)
# print(f"PDF {len(sections)} 页 → {len(chunks)} 个 chunk")
# print(f"Chunk0 前100字：{chunks[0][:100]}")

# 测试3
# import numpy as np
# from rag.embedding import EmbeddingModel
# EmbeddingModel.load()
# vec = EmbeddingModel.encode_query("政务公文管理办法")
# print("向量shape:", vec.shape)
# print("前10维向量值：", np.round(vec[:10],4))

#测试4
# from api.utils.vector_store import VectorStore
# import numpy as np

# vs = VectorStore("test1.index", dim=3)#role: 创建一个 3 维向量的 FAISS 索引
# # 写入 3 个向量，ID 分别是 a, b, c
# vs.add(np.array([[1,0,0], [0,1,0], [0,0,1]]), ["a", "b", "c"])
# print("ntotal after add:", vs.count())         # ← 加这行
# print("_id_list:", vs._id_list)                # ← 加这行
# vs.save()

# # 检索最接近 [0.9, 0.1, 0] 的 2 个向量
# results = vs.search(np.array([0.9, 0.1, 0]), top_k=2)
# print(results)  # [("a", 小距离), ("b", 中距离)]

#测试5
# from rag.llm.chat_model import ChatModel
# model = ChatModel()
# for token in model.stream_chat([{"role":"user","content":"你好"}]):
#     print(token, end="", flush=True)