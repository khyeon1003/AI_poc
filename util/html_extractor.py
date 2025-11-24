from bs4 import BeautifulSoup
import re

## 이미지& html 분리
def split_html_and_images(html: str):
  soup = BeautifulSoup(html, "lxml")
  image_urls = []
  placeholder_template = "[IMAGE_{}]"
  for idx, img in enumerate(soup.find_all("img")):
    src = img.get("src")
    if src:
      image_urls.append(src)
      img.replace_with(placeholder_template.format(idx))
    else:
      img.decompose()

  # body가 있으면 내부 내용만 반환, 없으면 전체
  if soup.body:
    html_without_imgs = "".join(str(child) for child in soup.body.contents)
  else:
    html_without_imgs = str(soup)

  return html_without_imgs, image_urls


## HTML parsing html -> text
def extract_text_from_html(html: str):
  soup = BeautifulSoup(html, "lxml")

  # 스크립트, 스타일 등 비본문 요소 제거
  for tag in soup(["script", "style", "noscript", "template"]):
      tag.decompose()

  # 줄바꿈 태그를 미리 변환
  for br in soup.find_all("br"):
      br.replace_with("\n")
  for p in soup.find_all("p"):
      # 문단 사이 구분 위해 뒤에 줄바꿈 추가
      p.append("\n")
  for li in soup.find_all("li"):
      li.insert_before("\n- ")  # 리스트 앞에 '- ' 붙이기
      li.append("\n")

  # 텍스트 추출 (separator="\n"은 태그 사이 줄바꿈 유지)
  text = soup.get_text(separator="\n")

  # 공백/빈 줄 정리
  text = re.sub(r"[ \t]+", " ", text)        # 연속 공백 1개로 축약
  text = re.sub(r"\n{3,}", "\n\n", text)     # 3줄 이상 빈 줄 → 2줄
  text = re.sub(r" *\n *", "\n", text)       # 줄 앞뒤 공백 제거
  text = text.strip()

  return text