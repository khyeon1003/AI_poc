import time
import uuid

from sqlalchemy.orm import Session

from config.config import settings
from config.open_ai_client import open_ai_client
from repositories.vector_repository import VectorRepository
from repositories.vector_retriever import VectorRetriever
from util.ansewer_evaluator import AnswerEvaluator
from util.embedding import Embedding
from util.query_expansion import ReformulationExpansion
from util.reranker import PassThroughRanker
from util.resp_text import _resp_text
import datetime

class ChatBot:
  def __init__(self):
    self.embedding=Embedding()
    self.reformulation=ReformulationExpansion()
    self.retriever=VectorRetriever()
    self.ranker=PassThroughRanker()
    self.client=open_ai_client
    ##평가 모델 추가]
    self.evaluator=AnswerEvaluator()
    self.db=VectorRepository()


  async def search(self,db:Session,query):
    #쿼리 익스텐션하고 ##이거는 따로 class 만들고
    expand_query= await self.reformulation.expand(query)
    ##쿼리 임베딩 -> 이거는 임베딩 단에서
    query_vec=self.embedding.query_to_embedding(expand_query["primary_query"])
    ##벡터 검색-> 따로 class로 일단 빼자
    ## 벡터 전처리
    query_vec=self._to_pgvector_literal(query_vec)
    ##Retriever
    retrieved_chunks = self.retriever.retrieve(db=db,query_vec=query_vec, top_k=20)
    ## ranker처리
    ranked = self.ranker.rank(expand_query["primary_query"], retrieved_chunks)
    final_contexts = ranked[:5] # 예: 상위 5개만 LLM에 전달

    return {
      "expand_query": expand_query,
      "retrieved_chunks": retrieved_chunks,
      "contexts": final_contexts,
    }
  ## 답변 생성
  async def answer(self,question,contexts):
    context_text = "\n\n---\n\n".join(ch.content for ch in contexts)

    prompt = f"""
      아래는 서울시립대학교 관련 공지/안내문 일부입니다. 이 정보를 기반으로 사용자의 질문에 답변해줘.
      
      답변을 생성할 때 다음 규칙을 반드시 지켜줘:
      
      1) 먼저 학생에게 친절하게 설명하는 "대화형 답변"을 2~3문장으로 제공한다.
         - 말투는 부드럽고 안내하는 톤으로
         - 핵심을 간단히 먼저 알려주기
      
      2) 그 아래에는 정보를 "정돈된 리스트 형식"으로 깔끔하게 요약해 준다.
         - '📌 제목' 형태의 소제목 사용
         - 각 항목은 "- 내용" 형태로 출력
         - 날짜/시간/방법/주의사항 등을 보기 좋게 줄바꿈해서 정리
         - Markdown 헤딩(#, ## 등)은 사용하지 말 것
      
      3) 문단과 항목 사이에는 반드시 "\\n\\n" 을 출력해 문단을 구분할 것.
         - 절대로 한 줄에 여러 정보를 이어붙이지 말 것
         - 각 항목도 반드시 새 줄에서 시작할 것
      
      4) 전체 답변은 하나의 텍스트로만 출력한다.
         (JSON 구조나 코드블록은 절대 사용하지 말 것)
      
      5) 너무 길게 설명하지 말고, 표나 공지사항처럼 핵심 위주로 요약한다.

      ---
      [컨텍스트]
      {context_text}

      [질문]
      {question}
      """

    response = self.client.responses.create(
        model=settings.OPENAI_MODEL,
        input=prompt,
    )

    answer = _resp_text(response).strip()

    return {
      "answer": answer,
      "contexts": [ch.content for ch in contexts],
    }
  ## 변환 함수
  @staticmethod
  def _to_pgvector_literal(vec) -> str:
    """
    [0.1, 0.2, 0.3] → "[0.1,0.2,0.3]"
    pgvector가 인식 가능한 문자열 리터럴로 변환
    """
    # numpy → list 변환
    if hasattr(vec, "tolist"):
      vec = vec.tolist()

    # float으로 캐스팅 + 문자열 조합
    return "[" + ",".join(str(float(x)) for x in vec) + "]"
  ##최종 채팅용 함수
  async def chat(self, db: Session, query: str) -> dict:

    """
    전체 플로우:
      1) search()로 컨텍스트 가져오기
      2) 휴리스틱으로 '아예 못 찾은 경우' early exit
      3) answer()로 1차 답변 생성
      4) AnswerEvaluator로 GOOD/BAD 판단
    """
    # 요청 단위 ID, 타임스탬프
    now = datetime.datetime.now(datetime.timezone.utc)
    request_id = f"rag-{now.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
    timestamp_iso = now.isoformat()

    overall_start = time.perf_counter()

    # 1) 검색
    search_result = await self.search(db, query)

    ##로그용
    expand_query = search_result["expand_query"]
    retrieved_chunks = search_result["retrieved_chunks"]
    contexts = search_result["contexts"]


    # context_used: 실제 LLM에 넘긴 상위 n개
    context_used = []
    for ch in contexts:
      url = self.db.get_document_url(db, ch.doc_id)
      context_used.append({
        "doc_id": str(ch.doc_id),
        "chunk_id": str(ch.chunk_id),
        "score": float(getattr(ch, "score", 0.0)),
        "url": url,
        "text_preview": ch.content,
      })

    #관련 URL들 (중복 제거)
    related_urls = sorted({
      item["url"]
      for item in context_used
      if item.get("url")  # None / 빈 문자열 제외
    })

    # --- 먼저 base_log 생성 (generation/evaluation은 나중에 채움)
    base_log = self._build_base_log(
      request_id=request_id,
      timestamp=timestamp_iso,
      top_k=len(retrieved_chunks),
      raw_query=query,
      rewritten_query=expand_query.get("primary_query"),
      retrieval_results=context_used,
    )

    # 휴리스틱: 컨텍스트가 없거나 너무 적으면 바로 "모르겠다" 처리
    if not contexts:
      final_answer = (
        "관련 공지를 찾지 못해서 정확한 답변을 드리기 어렵습니다. "
        "학교 공식 홈페이지 공지사항을 함께 확인해 주세요."
      )

      total_latency_ms = int((time.perf_counter() - overall_start) * 1000)

      base_log["generation"] = {
        "first_token_latency_ms": total_latency_ms,  # 비스트리밍이라 전체와 동일하게 기록
        "total_latency_ms": total_latency_ms,
        "final_answer": final_answer,
      }
      base_log["evaluation"] = {
        "verdict": "NO_CONTEXT",
        "score": 0.0,
        "detail": "no contexts retrieved",
      }

      self.db.save_rag_log(db,base_log)

      return {
        "answer": final_answer,
        "contexts": [],
        "eval": base_log["evaluation"],
        "meta": {
          "reason": "NO_CONTEXT",
          "heuristic": True,
          "related_urls": related_urls,
        },
      }

    # 휴리스틱: score 기반 최소 신뢰도 체크
    # VectorRetriever.RetrievedChunk에 score 필드 있다고 가정
    scores = [
      getattr(ch, "score", None) for ch in contexts
      if getattr(ch, "score", None) is not None
    ]
    max_score = max(scores) if scores else 0.0

    # 예시: max_score가 0.4 아래면 "관련성 낮음"으로 보고 그냥 보수적인 답변
    if max_score < 0.4:
      final_answer = (
        "질문과 직접적으로 관련된 공지를 충분히 찾지 못했습니다. "
        "정확한 내용은 학교 공식 공지사항을 다시 확인해 주세요."
      )

      total_latency_ms = int((time.perf_counter() - overall_start) * 1000)

      base_log["generation"] = {
        "first_token_latency_ms": total_latency_ms,
        "total_latency_ms": total_latency_ms,
        "final_answer": final_answer,
      }
      base_log["evaluation"] = {
        "verdict": "LOW_RETRIEVAL_SCORE",
        "score": float(max_score),
        "detail": "max_score below threshold 0.4",
      }

      self.db.save_rag_log(db,base_log)

      return {
        "answer": final_answer,
        "contexts": [ch.content for ch in contexts],
        "eval": base_log["evaluation"],
        "meta": {
          "reason": "LOW_RETRIEVAL_SCORE",
          "max_score": max_score,
          "heuristic": True,
          "related_urls": related_urls,
        },
      }

    # 2) 1차 답변 생성
    ##시간 측정용
    llm_start = time.perf_counter()
    answer_payload = await self.answer(question=query, contexts=contexts)
    ##시간 측정용
    llm_end = time.perf_counter()
    answer_text = answer_payload["answer"]

    # 3) evaluator용 context summary (지금은 그냥 content를 짧게 잘라서 사용)
    #   - 나중에 chunk에 eval_summary 필드 만들면 그걸 쓰면 됨
    eval_context_summaries = [
      ##이후 요약본 만들어서 요약본 사용하기
      ch.content[:400]  # 너무 길지 않게 앞부분만 사용 (문자 기준 대략)
      for ch in contexts[:3]  # 상위 3개만 평가에 사용
    ]

    eval_result = self.evaluator.evaluate(
      question=query,
      answer=answer_text,
      context_summaries=eval_context_summaries,
    )

    # 4) verdict 따라 후처리 (지금은 BAD여도 일단 답변은 주되, 메타에 표시)
    verdict = eval_result.get("verdict", "BAD")

    # BAD일 때 경고 문구 살짝 붙여주기 (선택사항)
    if verdict == "BAD":
      safe_answer = (
        answer_text
        + " "
        + "(⚠️ 이 답변은 제공된 공지와 정확히 일치하지 않을 수 있습니다. 중요한 내용은 반드시 공식 공지 원문을 함께 확인해 주세요.)"
      )
      answer_payload["answer"] = safe_answer
    # 6) generation/evaluation 로그 채우기
    total_latency_ms = int((time.perf_counter() - overall_start) * 1000)
    first_token_latency_ms = int((llm_end - llm_start) * 1000)
    # 최종 반환 구조: answer + contexts + eval 메타
    base_log["generation"] = {
      "first_token_latency_ms": first_token_latency_ms,
      "total_latency_ms": total_latency_ms,
      "final_answer": answer_text,
    }
    base_log["evaluation"] = eval_result

    self.db.save_rag_log(db, base_log)

    return {
      "answer": answer_payload["answer"],
      "contexts": answer_payload["contexts"],
      "eval": eval_result,
      "meta": {
        "max_retrieval_score": max_score,
        "used_heuristic": False,  # 위에서 early-return 한 케이스만 True
        "verdict": verdict,
        "related_urls": related_urls,
      },
    }

  def _build_base_log(
      self,
      *,
      request_id: str,
      timestamp: str,
      top_k: int,
      raw_query: str,
      rewritten_query: str | None,
      retrieval_results: list[dict],
  ) -> dict:
    return {
      "metadata": {
        "request_id": request_id,
        "timestamp": timestamp,
        "retrival_top_k": top_k,
      },
      "query": {
        "raw": raw_query,
        "rewritten": rewritten_query,
      },
      "retrieval_used": {
        "results": retrieval_results,
      },
      # "generation": ...   # 아래에서 채움
      # "evaluation": ...   # 아래에서 채움
    }

