from sqlalchemy.orm import Session
from models import Document, DocChunk


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