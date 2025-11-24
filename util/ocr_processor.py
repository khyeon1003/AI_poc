from typing import List
from config.config import settings
from config.open_ai_client import open_ai_client
from util.resp_text import _resp_text


class OCRProcessor:
  def __init__(self):
    self.client=open_ai_client

  def ocr_openai_extract_many_urls(
      self,
      urls: List[str],
      per_image_prompt: str = "Extract all readable text from this image. Return plain text only; keep line breaks."
  ) -> List[str]:
    """
    📑 각 이미지 URL을 개별 호출로 OCR 처리하는 함수
    - 입력: 이미지 URL 리스트
    - 출력: 각 이미지별 OCR 결과 리스트 (순서 동일)
    - 장점: 대량 이미지나 병렬처리에 유리, 실패 시 개별 에러 확인 가능
    """
    results: List[str] = []

    for u in urls:
      content = [
        {"type": "input_text", "text": per_image_prompt},
        self._to_image_part_url(u),
      ]
      try:
        resp = self.client.responses.create(
            model=settings.OPENAI_MODEL,
            input=[{"role": "user", "content": content}],
        )
        results.append(_resp_text(resp).strip())
      except Exception as e:
        results.append(f"[OCR_ERROR] {u} :: {e}")

    return results

  ## 이미지 추출 함수
  @staticmethod
  def _to_image_part_url(url: str) -> dict:
    """
    🔹 OpenAI Responses API에서 이미지 입력 형식으로 변환하는 함수
    - 입력: http(s) URL 문자열
    - 출력: {"type": "input_image", "image_url": {"url": url}} 형태의 딕셔너리
    - 주의: URL은 외부에서 접근 가능한 공개 주소여야 함 (S3 presigned 등)
    """
    if not (url.startswith("http://") or url.startswith("https://")):
      raise ValueError(f"Not a valid http(s) URL: {url}")
    return {"type": "input_image", "image_url": url}


