from typing import List
from sqlalchemy import text
from dataclasses import dataclass
from sqlalchemy.orm import Session

@dataclass
class RetrievedChunk:
    chunk_id: str
    doc_id: str
    content: str
    score: float


class VectorRetriever:

  def retrieve(
      self,
      db: Session,
      query_vec,
      top_k: int = 20,
  ) -> List[RetrievedChunk]:
    sql = text("""
               SELECT c.chunk_id                             AS chunk_id,
                      c.doc_id,
                      c.text,
                      1 - (c.embedding <=> :query_vec) AS score
               FROM doc_chunks c
               ORDER BY c.embedding <=> :query_vec
          LIMIT :top_k
               """)

    rows = db.execute(
        sql,
        {
          "query_vec": query_vec,
          "top_k": top_k,
        },
    ).mappings().all()

    return [
      RetrievedChunk(
          chunk_id=row["chunk_id"],
          doc_id=row["doc_id"],
          content=row["text"],
          score=row["score"],
      )
      for row in rows
    ]