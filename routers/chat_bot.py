from fastapi import APIRouter

routers= APIRouter(prefix="chat_bot",tags=["chat_bot"])

# @routers.post("/") # 유저 req 추가
# async def create_chat_bot(request: ChatRequest):
#     try:
