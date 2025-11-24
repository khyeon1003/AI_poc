# routers/chat_router.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette.responses import HTMLResponse

from database import get_db
from schemas.chat_ragas_dto import RagasChatRequest
from services.chatbot_service import ChatBot  # 네가 구현해둘 서비스 사용

router = APIRouter(
    prefix="/api",
    tags=["chat"],
)

chat_bot_service = ChatBot()

@router.post("/chat")
async def chat(body: dict, db: Session = Depends(get_db)):
    query = body.get("query")

    if not query:
        return {"error": "query is required"}

    result = await chat_bot_service.chat(db=db, query=query)

    return result

##ragas 평가용
@router.post("/chat_ragas")
async def chat(request: RagasChatRequest, db: Session = Depends(get_db)):
  # request.question, request.conversation_id 로 접근 가능
  question = request.question
  conv_id = request.conversation_id

  result = await chat_bot_service.chat(
      db=db,
      query=question,
  )

  response = {
    "answer": result.get("answer"),
    "contexts": result.get("contexts", [])
  }

  return response


# 🔽 UI용 엔드포인트 (GET /)
@router.get("/", response_class=HTMLResponse)
async def chat_page():
    return """
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <title>UOSLIFE 공지 챗봇</title>

  <style>
    * { box-sizing: border-box; }

    body {
      margin: 0;
      padding: 0;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #f3f4f6;
    }

    .app {
      max-width: 900px;
      margin: 40px auto;
      padding: 24px;
      background: #ffffff;
      border-radius: 18px;
      box-shadow: 0 10px 25px rgba(0,0,0,0.06);
    }

    .header { margin-bottom: 20px; }

    .title {
      font-size: 22px;
      font-weight: 700;
      margin: 0 0 4px;
    }

    .subtitle {
      font-size: 13px;
      color: #6b7280;
      margin: 0;
    }

    .input-card {
      border-radius: 14px;
      padding: 16px 18px 18px;
      background: #f9fafb;
      border: 1px solid #e5e7eb;
      margin-bottom: 20px;
    }

    label {
      font-size: 13px;
      font-weight: 600;
      color: #4b5563;
      display: block;
      margin-bottom: 6px;
    }

    textarea {
      width: 100%;
      min-height: 70px;
      resize: vertical;
      font-size: 14px;
      padding: 10px 12px;
      border-radius: 10px;
      border: 1px solid #d1d5db;
      outline: none;
      transition: border-color 0.15s, box-shadow 0.15s;
    }

    textarea:focus {
      border-color: #2563eb;
      box-shadow: 0 0 0 2px rgba(37,99,235,0.15);
      background: #ffffff;
    }

    .btn-row {
      margin-top: 10px;
      display: flex;
      justify-content: flex-end;
    }

    button {
      border: none;
      border-radius: 999px;
      padding: 8px 18px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      background: #2563eb;
      color: #ffffff;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      box-shadow: 0 4px 10px rgba(37,99,235,0.25);
      transition: background 0.15s, transform 0.06s, box-shadow 0.15s;
    }

    button:hover {
      background: #1d4ed8;
      box-shadow: 0 6px 14px rgba(37,99,235,0.3);
      transform: translateY(-1px);
    }

    .error {
      color: #dc2626;
      font-size: 12px;
      margin-top: 6px;
    }

    .answer-card {
      margin-top: 10px;
      padding: 18px 20px;
      border-radius: 14px;
      border: 1px solid #e5e7eb;
      background: #ffffff;
    }

    .answer-title {
      font-size: 14px;
      font-weight: 600;
      color: #374151;
      margin-bottom: 10px;
    }

    .answer-box {
      font-size: 15px;
      line-height: 1.7;
      color: #111827;
      white-space: pre-wrap; /* 줄바꿈·리스트 그대로 살리기 */
    }

    .related {
      margin-top: 18px;
      padding: 14px 16px;
      border-radius: 12px;
      background: #f9fafb;
      border: 1px dashed #d1d5db;
    }

    .related h2 {
      font-size: 13px;
      font-weight: 600;
      color: #4b5563;
      margin: 0 0 6px;
    }

    .related ul {
      margin: 0;
      padding-left: 18px;
      font-size: 13px;
    }

    .related a {
      color: #2563eb;
      text-decoration: none;
      word-break: break-all;
    }

    .related a:hover {
      text-decoration: underline;
    }
  </style>
</head>
<body>
  <div class="app">
    <header class="header">
      <h1 class="title">UOSLIFE 공지 챗봇</h1>
      <p class="subtitle">공지 기반 학사 일정/수강신청/장학금/일정 검색 서비스</p>
    </header>

    <section class="input-card">
      <label for="query">질문</label>
      <textarea id="query" placeholder="예) 2025년 1학기 수강신청 일정 알려줘"></textarea>

      <div class="btn-row">
        <button id="sendBtn">질문 보내기 ↗</button>
      </div>

      <div id="error" class="error"></div>
    </section>

    <section class="answer-card">
      <div class="answer-title">답변</div>
      <div class="answer-box" id="answer">질문을 입력하면 이곳에 답변이 표시됩니다.</div>

      <div class="related" id="related" style="display:none;">
        <h2>관련 게시물</h2>
        <ul id="relatedList"></ul>
      </div>
    </section>
  </div>

  <script>
    const queryInput = document.getElementById("query");
    const sendBtn = document.getElementById("sendBtn");
    const answerBox = document.getElementById("answer");
    const errorBox = document.getElementById("error");
    const relatedBox = document.getElementById("related");
    const relatedList = document.getElementById("relatedList");

    function renderRelatedUrls(meta) {
      relatedList.innerHTML = "";
      relatedBox.style.display = "none";

      if (!meta || !Array.isArray(meta.related_urls)) return;

      meta.related_urls.forEach(url => {
        const li = document.createElement("li");
        const a = document.createElement("a");
        a.href = url;
        a.target = "_blank";
        a.textContent = url;
        li.appendChild(a);
        relatedList.appendChild(li);
      });

      if (meta.related_urls.length > 0) {
        relatedBox.style.display = "block";
      }
    }

    async function sendQuery() {
      const query = queryInput.value.trim();
      errorBox.textContent = "";
      answerBox.textContent = "⏳ 답변 생성 중...";

      relatedList.innerHTML = "";
      relatedBox.style.display = "none";

      if (!query) {
        errorBox.textContent = "질문을 입력해 주세요.";
        answerBox.textContent = "질문을 입력하면 이곳에 답변이 표시됩니다.";
        return;
      }

      try {
        // 이 HTML이 /api/v1/ 아래에 매달려 있다면,
        // 같은 router에 있는 POST /chat 으로 상대 경로 요청됨
        const res = await fetch("chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query }),
        });

        if (!res.ok) throw new Error("서버 오류: " + res.status);

        const data = await res.json();

        // LLM answer 그대로 보여주기 (프롬프트에서 예쁘게 정리하도록 강제)
        answerBox.textContent = data.answer || "답변이 없습니다.";
        renderRelatedUrls(data.meta);

      } catch (err) {
        errorBox.textContent = "에러 발생: " + err.message;
        answerBox.textContent = "답변을 가져오지 못했습니다.";
      }
    }

    sendBtn.addEventListener("click", sendQuery);

    queryInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendQuery();
      }
    });
  </script>

</body>
</html>
    """

