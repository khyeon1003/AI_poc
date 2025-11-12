import uuid

from sqlalchemy import Column, UUID, String, JSON, DateTime, func

from database import Base


class Document(Base):
  __tablename__ = "documents"

  doc_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  title = Column(String, nullable=False)
  text = Column(String)
  document_metadata = Column(JSON)
  created_at = Column(DateTime(timezone=True), server_default=func.now())
