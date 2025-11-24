from typing import List
import json

from config.config import settings
from config.open_ai_client import open_ai_client as client

EVAL_SYSTEM_PROMPT = """\
You are a strict judge for a RAG chatbot.
Use ONLY the given contexts as ground-truth.

Decide:
1) Is the answer factually supported by the contexts?
2) Does it correctly answer the user's question?

Return JSON only.
"""

EVAL_USER_PROMPT_TEMPLATE = """\
[QUESTION]
{question}

[ANSWER]
{answer}

[CONTEXT SUMMARIES]
{contexts_block}

[OUTPUT FORMAT]
{{
  "verdict": "GOOD" | "BAD",
  "reason": "짧은 한국어 설명",
  "should_regenerate": true | false
}}
"""


class AnswerEvaluator:
  def __init__(
      self,
      ##기준치
      threshold: float = 0.8,  # 사실상 안 쓰고, 모델이 verdict만 내리게 해도 됨
  ):
    # 설정에 별도 eval 모델이 있으면 우선 사용, 없으면 기본 모델
    self.model = settings.OPENAI_EVAL_MODEL
    self.threshold = threshold

  def build_prompt(self, question: str, answer: str,
      context_summaries: List[str]) -> str:
    contexts_block = "\n".join(
        [f"- {c}" for c in context_summaries]
    )
    return EVAL_USER_PROMPT_TEMPLATE.format(
        question=question,
        answer=answer,
        contexts_block=contexts_block,
    )

  def evaluate(self, question: str, answer: str,
      context_summaries: List[str]) -> dict:
    if not context_summaries:
      # 컨텍스트 없으면 그냥 BAD로 보고 재생성 or "모르겠다" 처리
      return {
        "verdict": "BAD",
        "reason": "관련 컨텍스트가 없습니다.",
        "should_regenerate": True,
      }

    user_prompt = self.build_prompt(question, answer, context_summaries)

    resp = client.chat.completions.create(
        model=self.model,
        temperature=0.0, # 창의성을 0으로 만드는 옵션
        messages=[
          {"role": "system", "content": EVAL_SYSTEM_PROMPT},
          {"role": "user", "content": user_prompt},
        ],
    )

    content = resp.choices[0].message.content.strip() ##함수 내가 만든걸로 바꿀수 있을거 같은데
    start = content.find("{")
    end = content.rfind("}")
    data = json.loads(content[start:end + 1])

    # 방어 코드
    if "verdict" not in data:
      data["verdict"] = "BAD"
      data["should_regenerate"] = True
      data["reason"] = data.get("reason", "평가 JSON 형식 오류")

    return data
