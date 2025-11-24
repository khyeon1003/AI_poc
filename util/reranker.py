from typing import List
from repositories.vector_retriever import RetrievedChunk

class PassThroughRanker:
    name = "pass_through"

    def rank(self, question: str, chunks: List[RetrievedChunk]) -> List[RetrievedChunk]:
        # retriever에서 이미 score 순 정렬이면 그대로 리턴
        return chunks