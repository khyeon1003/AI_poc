# schemas/rag_log.py
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class RagMetadata(BaseModel):
    request_id: str
    timestamp: datetime
    top_k: int
    embedding_model: str
    search_filters: Dict[str, Any] = Field(default_factory=dict)


class RagQuery(BaseModel):
    raw: str
    rewritten: Optional[str] = None


class RetrievalResult(BaseModel):
    doc_id: str
    score: float
    url: Optional[str] = None
    text_preview: Optional[str] = None


class RagRetrieval(BaseModel):
    results: List[RetrievalResult]

class RagGeneration(BaseModel):
    model: str
    first_token_latency_ms: Optional[int] = None
    total_latency_ms: int
    final_answer: str


class RagLog(BaseModel):
    metadata: RagMetadata
    query: RagQuery
    retrieval: RagRetrieval
    generation: RagGeneration
