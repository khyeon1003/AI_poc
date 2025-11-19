#main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from config.hnsw_index_config import init_hnsw_index
from database import Base, engine
# 테이블 자동 생성


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

@app.get("/")
async def root():
    return {"message": "Hello World"}