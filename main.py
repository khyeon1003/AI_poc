#main.py
from fastapi import FastAPI

from database import Base, engine

from models import Document,DocChunk

# 테이블 자동 생성

app = FastAPI()

Base.metadata.create_all(bind=engine)

@app.get("/")
async def root():
    return {"message": "Hello World"}