# models/rag_log.py
import uuid
from sqlalchemy import Column, DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from database import Base

class RagLogModel(Base):
    __tablename__ = "rag_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(String, index=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    log = Column(JSONB, nullable=False)  # RagLog 전체를 그대로 넣는 필드
