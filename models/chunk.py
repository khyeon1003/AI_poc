from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from database import Base

class DocChunk(Base):
  __tablename__ = "doc_chunks"

  chunk_id = Column(Integer, primary_key=True, index=True)
  doc_id = Column(UUID(as_uuid=True),
                  ForeignKey("documents.doc_id", ondelete="CASCADE"))
  chunk_index = Column(Integer, nullable=False)
  text = Column(String)
  model = Column(String)
  dim = Column(Integer)
  embedding = Column(Vector(1024))