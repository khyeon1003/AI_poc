## 임베딩 처리
## 싱글 톤으로 해야 하나,,?
from urllib.parse import urljoin

from bs4 import BeautifulSoup



class Embedding:
  def __init__(self):
    pass

  #전처리
  ## HTML& 이미지 분리
  @staticmethod # 정적 메서드 처리를 해야 self 없이 사용 가능
  def split_html_and_images(html):

    soup = BeautifulSoup(html, "lxml")
    image_urls=[]
    for img in soup.find_all("img"):
      src=img.get("src")
      if src:
        image_urls.append(src)
      img.decompose()

    # body가 있으면 내부 내용만 반환, 없으면 전체
    if soup.body:
      html_without_imgs = "".join(str(child) for child in soup.body.contents)
    else:
      html_without_imgs = str(soup)

    return html_without_imgs, image_urls


  ## HTML parsing html ->

  ## 이미지 OCR


  ## 제목+ 본문 데이터-> 청킹

  ## 청킹 데이터 -> API로 임베딩

  ##고민: 메타 데이터 처리 방안?

