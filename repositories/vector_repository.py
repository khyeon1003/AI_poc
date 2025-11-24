import uuid

from sqlalchemy.orm import Session
from models import Document, DocChunk
from models.rag_log import RagLogModel


class VectorRepository:

  def create_document(
      self,
      db:Session,
      title: str,
      text: str,
      metadata: dict
  ) -> Document:
    doc = Document(
        title=title,
        text=text,
        document_metadata=metadata,
    )
    db.add(doc)
    db.flush()  # PK(doc_id) 생성
    return doc

  def create_chunks(self, db:Session, doc_id, model_name, dim, chunks):
    for c in chunks:
      db.add(DocChunk(
          doc_id=doc_id,
          chunk_index=c["chunk_index"],
          text=c["embed"],
          model=model_name,
          dim=dim,
          embedding=c["embedding"],
      ))

  def commit(self, db: Session):
    db.commit()

  def refresh(self, db: Session, doc: Document):
    db.refresh(doc)

  def save_rag_log(self,db: Session, log_data: dict):
    """
    log_data는 네가 정의한 JSON 그대로:
    {
      "metadata": {...},
      "query": {...},
      "retrieval": {...},
      ...
    }
    """

    request_id = log_data["metadata"]["request_id"]

    rag_log = RagLogModel(
        request_id=request_id,
        log=log_data,
    )

    db.add(rag_log)
    db.commit()
    db.refresh(rag_log)
    return rag_log

  def get_document_url(self, db: Session,
      doc_id: str | uuid.UUID) -> str | None:
    """
    doc_id를 받아 documents 테이블에서 metadata.url을 가져오는 함수
    """
    doc = (
      db.query(Document)
      .filter(Document.doc_id == doc_id)
      .first()
    )
    if not doc:
      return None

    metadata = getattr(doc, "document_metadata", None)
    if not metadata:
      return None

    return metadata.get("url")