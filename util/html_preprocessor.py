from util.html_extractor import extract_text_from_html, split_html_and_images
from util.ocr_processor import OCRProcessor


class HtmlPreprocessor:
  def __init__(self):
    self.ocr = OCRProcessor()

  async def process(self, html: str) -> str:
    """
    1) HTML에서 이미지 플레이스홀더와 본문 HTML 추출
    2) HTML → 텍스트 변환 (이미지 제외)
    3) 이미지 URL 각각 OCR 실행
    4) 플레이스홀더 위치에 OCR 텍스트 삽입
    """

    # 1. HTML 분리
    html_without_imgs, image_urls = split_html_and_images(html)

    # 2. 텍스트 추출
    base_text = extract_text_from_html(html_without_imgs)

    # 이미지 없으면 바로 리턴
    if not image_urls:
      return base_text

    # 3. OCR 처리
    # (동기 OCR 사용 중 → 필요하면 async 로 개선 가능)
    from typing import List
    ocr_results: List[str] = self.ocr.ocr_openai_extract_many_urls(image_urls)

    # 4. 플레이스홀더 치환
    merged = base_text
    for idx, ocr_text in enumerate(ocr_results):
      placeholder = f"[IMAGE_{idx}]"
      replacement = f"\n\n[IMAGE OCR]\n{ocr_text}\n\n"
      merged = merged.replace(placeholder, replacement)

    return merged.strip()