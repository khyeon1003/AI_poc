## 임베딩 처리
from typing import List, Dict
import numpy as np
from config.huggingface_client import huggingface_client


class Embedding:
  def __init__(self):
    self.huggingface = huggingface_client
    self.model="intfloat/multilingual-e5-large"
    self.prefix="passage"

## 청킹 데이터 -> API로 임베딩
  def chunk_to_embedding(self,chunks: List[Dict], batch_size: int = 8):
    texts = [f"{self.prefix}: {c['embed']}" for c in chunks]
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
      batch = texts[i:i + batch_size]
      print(f"batch: {batch}")
      vecs = self.huggingface.feature_extraction(batch,model=self.model)  # (B, 1024)
      print(f"vecs: {vecs}")
      all_embeddings.extend(vecs)

    # 정규화(코사인 유사도용)
    all_embeddings = self.l2_normalize(all_embeddings)

    # 원래 청크와 결합
    out = []
    for c, emb in zip(chunks, all_embeddings):
      out.append({**c, "embedding": emb})
    return out

  ## 정규화용
  @staticmethod
  def l2_normalize(vecs: List[List[float]]) -> List[List[float]]:
    arr = np.array(vecs, dtype=np.float32)
    norms = np.linalg.norm(arr, axis=1, keepdims=True) + 1e-12
    return (arr / norms).tolist()

  def query_to_embedding(self,query:str,prefix: str= "query"):
    prefix_query=f"{prefix}:{query}"
    print(f"prefix_query: {prefix_query}")
    vecs = self.huggingface.feature_extraction(prefix_query,model=self.model)
    result = self.l2_normalize(vecs)
    return result



