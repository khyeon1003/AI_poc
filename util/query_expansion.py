from abc import ABC, abstractmethod
from typing import Dict
from config.open_ai_client import open_ai_client
from config.config import settings
from util.resp_text import _resp_text
from datetime import datetime


## 추상 class
class QueryExpansionStrategy(ABC):
    name: str

    def __init__(self):
      self.client = open_ai_client

    @abstractmethod
    async def expand(self, question: str) -> Dict:
        """
        return 예시:
        {
          "primary_query": "검색에 쓸 대표 쿼리",
          "queries": ["쿼리1", "쿼리2", ...],  # multi-query인 경우
          "sub_questions": [...],             # decomposition인 경우
          "meta": {...}
        }
        """

##Reformulation 방식-> 일단 1차적으로 이방식을 쓴다고 생각
class ReformulationExpansion(QueryExpansionStrategy):
  name = "reformulation"

  def __init__(self):
    super().__init__()

  async def expand(self, question: str) -> Dict:
    ##시간 추론
    now = datetime.now()
    current_year = now.year
    current_month = now.month

    # 학기 자동 계산
    if current_month <= 6:
      current_semester = "1학기"
    else:
      current_semester = "2학기"

    prompt = f"""
        사용자의 질문을 벡터 검색에 적합한 형태로 재작성해줘.
        - 불필요한 말투, 감탄사는 제거
        - 학교명, 연도, 학기 등은 최대한 명시
        - 학기/연도가 없다면 다음 값을 사용:
        - 연도: {current_year}
        - 학기: {current_semester}
        - 한 문장으로만 출력

        질문: "{question}"
        재작성된 검색용 쿼리:
        """

    response = self.client.responses.create(
            model=settings.OPENAI_MODEL,
            input=[{"role": "user", "content": prompt}],
        )

    rewritten = _resp_text(response).strip().replace("\n", " ")

    return {
      "primary_query": rewritten,
      "queries": [rewritten],
      "sub_questions": [],
      "meta": {
        "raw": question,
        "rewritten": rewritten,
      }
    }

##Muti Query 방식-> 여러번 검색후 재정렬하면됨=> 이거는 잘 안나올때 적용하기
class MultiQueryExpansion(QueryExpansionStrategy):
  name = "multi_query"

  def __init__(self, n: int = 3):
    super().__init__()
    self.n = n

  async def expand(self, question: str) -> Dict:
    prompt = f"""
      사용자의 질문을 벡터 검색용으로 {self.n}가지 다른 표현으로 재작성해줘.
      - 의미는 유지하되, 표현과 초점을 조금씩 다르게
      - 각 줄에 하나씩, 번호 없이 출력

      질문: "{question}"
      """

    response = self.client.responses.create(
        model=settings.OPENAI_MODEL,
        input=[{"role": "user", "content": prompt}],
    )
    queries = [line.strip() for line in response.split("\n") if line.strip()]

    # n개 넘으면 자르기
    queries = queries[: self.n]

    primary = queries[0] if queries else question

    return {
      "primary_query": primary,
      "queries": queries,
      "sub_questions": [],
      "meta": {
        "raw": question,
        "variants": queries
      }
    }

