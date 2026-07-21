import os
import uuid
import tempfile
from typing import Optional

from api.celery_app import celery
from api.db.db_models import db, Document, Chunk
from api.utils.s3_client import download_file
from api.utils.vector_store import VectorStore
from deepdoc.parser.pdf_parser import PdfParser
from deepdoc.chunker.naive_chunker import naive_merge
from rag.embedding import EmbeddingModel

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "faiss")


@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def parse_document(self, doc_id: str):
    """对标 RAGFlow task_executor.do_handle_task() —— 异步文档解析流水线"""
    doc = Document.query.get(doc_id)
    if not doc:
        return

    doc.status = "parsing"
    db.session.commit()

    tmp_path: Optional[str] = None

    try:
        tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        tmp_path = tmp.name
        tmp.close()

        download_file(doc.file_path, tmp_path)

        sections = PdfParser.parse(tmp_path)
        chunks = naive_merge(sections, chunk_token_num=512)

        EmbeddingModel.load()
        vectors = EmbeddingModel.encode(chunks)

        index_dir = os.path.join(_DATA_DIR, str(doc.dataset_id))
        vs = VectorStore(index_dir)
        chunk_ids = [str(uuid.uuid4()) for _ in chunks]
        vs.add(vectors, chunk_ids)
        vs.save()

        for idx, (cid, text) in enumerate(zip(chunk_ids, chunks)):
            token_count = len(text)
            db.session.add(Chunk(
                id=cid,
                tenant_id=doc.tenant_id,
                document_id=doc.id,
                dataset_id=doc.dataset_id,
                content=text,
                token_count=token_count,
                chunk_index=idx,
            ))

        doc.status = "ready"
        doc.chunk_count = len(chunks)
        doc.token_count = sum(len(t) for t in chunks)
        db.session.commit()

    except Exception:
        db.session.rollback()
        if doc and doc.id:
            doc.status = "error"
            db.session.commit()
        raise self.retry()

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
