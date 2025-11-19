from sqlalchemy.orm import Session

from repositories.vector_repository import VectorRepository
from util.chunker import Chunker
from util.embedding import Embedding
from util.html_preprocessor import HtmlPreprocessor
from typing import List
from typing import Dict


class VectorService:
    def __init__(self):
      self.repo=VectorRepository()
      self.embedding=Embedding()
      self.chunker=Chunker()
      self.html_parser=HtmlPreprocessor()

    async def create_vector(self, db: Session,title, html, metadata):
      ## 전처리
      processed_text: str = await self.html_parser.process(html)
      ## 청킹
      chunks: List[Dict] = self.chunker.chunk(
          title=title,
          text=processed_text,
      )

      ##임베딩
      chunks_with_emb: List[Dict] = self.embedding.chunk_to_embedding(
          chunks=chunks,
          batch_size=8,
      )

      dim = len(chunks_with_emb[0]["embedding"])

      ##레포 doc 저장
      doc = self.repo.create_document(db, title=title, text=processed_text,
                                      metadata=metadata)
      ##청크 저장
      self.repo.create_chunks(db, doc_id=doc.doc_id,
                              model_name=self.embedding.model,
                              dim=dim, chunks=chunks_with_emb)
      self.repo.commit(db)
      self.repo.refresh(db, doc)

      return doc.doc_id


