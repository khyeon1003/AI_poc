# schemas/chat.py
from typing import Any, Dict, List
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(..., description="사용자 질문")
    top_k: int = Field(5, description="가져올 컨텍스트 청크 개수")


class RetrievedChunkOut(BaseModel):
    chunk_id: str
    doc_id: str
    content: str
    score: float
    metadata: Dict[str, Any]


class ChatResponse(BaseModel):
    answer: str
    contexts: List[RetrievedChunkOut]
