#main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from config.hnsw_index_config import init_hnsw_index
from database import Base, engine
# 테이블 자동 생성
from models.document import Document  # noqa: F401
from models.chunk import DocChunk
from models.rag_log import RagLogModel
from routers.vector_router import router as vector_router
from routers.chatbot_router import router as chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- startup ---
    Base.metadata.create_all(bind=engine)
    init_hnsw_index()
    print("HNSW Index initialized")

    yield

    # --- shutdown ---
    print("Shutting down...")

app = FastAPI(lifespan=lifespan)


app.include_router(vector_router)
app.include_router(chat_router)

@app.get("/")
async def root():
    return {"message": "Hello World"}