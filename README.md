# AI_poc
![ezgif-3d0f472a9d166a2d](https://github.com/user-attachments/assets/b09ff36f-fbbf-4dad-be7c-b3f939242d88)

## 데이터 처리 (Ingestion)

- html 파싱
    - `BeautifulSoup` 를 활용하여 html 파싱
    - 이미지 존재시 [IMAGE] 태그로 위치 기억
- OCR
    - 모델: `gpt-4o`
    - 프롬프트: `"Extract all readable text from this image. Return plain text only; keep line breaks."`
    - 활용하여 이미지 OCR 처리
    - 모듈 방식(`pytesseract`)으로 처리해보고자 했으나 정확도가 너무 낮아 open ai로 대체

**⇒ 두가지 작업 이후 하나의 text를 만들어 청킹 진행**

- chunking
    - **`기준`**
        - 줄바꿈 정리
        - 문단 기준 1차 분리
            
            빈 줄 2개 이상 → 문단 단위로 분할.
            
        - 숫자 항목 기준 2차 분리
            
            `1.`, `2)`, `①`, `Ⅰ.` 같은 번호 목록이 있으면 각 항목을 독립 조각으로 분리.
            
        - 토큰 한도 초과 시 슬라이딩 윈도우
            
            한 조각이 `max_tokens` 넘으면 오버랩(`overlap_tokens`) 적용해서 문자 단위로 윈도우 잘라냄.
            
        - 너무 짧은 조각 병합
            
            `min_tokens` 미만이면 앞 조각에 합쳐서 짧은 청크 난생 방지.
            
    - 최종 임베딩 텍스트 구성
        
        ```
        [TITLE] 제목
        [CHUNK] 본문
        ```
        
- embedding
    - 모델: `intfloat/multilingual-e5-large` ⇒ 한국어 지원이 잘되는 모델로 설정
    - 정규화
        - 벡터간 연산(코사인 유사도)을 하기 위해 차원을 정규화 필요
        - **`1024 차원`**으로 정규화
    - 인덱싱
        - 검색시 찾는 시간을 줄이기 위해 **HNSW 인덱싱 방식** 사용
        - 저장시 시간이 오래걸린다는 단점 존재
- DB
    - pgvector 사용

## 검색 Search

- query expasion
    - `gpt-4o` 모델을 활용하여 query 확장을 진행
    - `prompt`
        
        ```
           사용자의 질문을 벡터 검색에 적합한 형태로 재작성해줘.
                - 불필요한 말투, 감탄사는 제거
                - 학교명, 연도, 학기 등은 최대한 명시
                - 학기/연도가 없다면 다음 값을 사용:
                - 연도: {current_year}
                - 학기: {current_semester}
                - 한 문장으로만 출력
        
                질문: "{question}"
                재작성된 검색용 쿼리:
        ```
        
- retriever
    - **`코사인 유사도 검색`**을 활용하여 Top-k 20개를 추출
    - 이후 상위 5개의 chunk를 contexts로 활용
    - 20개 추출의 이유는 현재는 `reranker`를 따로 진행하고 있지 않지만 이후 확장성을 위해 추출
- ansewer
    - `gpt-4o` 모델을 활용하여 답변 생성
    - `prompt` 를 통해 답변 가이드라인 생성
- evaluation
    - 답변 생성후 `gpt-4o-mini` 모델을 활용하여 evalution을 진행
    - eval 경우
        - context 없을 경우⇒ 관련 정보 없음
        - eval을 진행 후 BAD 일 경우 **`or`** max chunk의 score가 0.4 이하 일경우 ⇒ 정보제공 but 추가 확인 요청
        - eval을 진행 후 GOOD 일경우 ⇒ 정보제공
    - 이후 `regeneration` 까지 확장 필

---

## backlog

- 시멘틱 검색 전 필터링
- reranker 고민
- 토큰 계산& 비용 계산 하기
- lantency 줄이기
- 가드레일 잡기(토큰 낭비 제한,답변 불가능 등)
- 테이블 재구성하기
