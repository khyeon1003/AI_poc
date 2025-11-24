import os
from dotenv import load_dotenv

load_dotenv()  # .env 파일 로드

class Settings:
  OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
  OPENAI_MODEL: str = os.getenv("OPENAI_MODEL")
  OPENAI_EVAL_MODEL: str = os.getenv("OPENAI_EVAL_MODEL")
  ##허깅 페이스 세팅
  HUGGING_FACE_KEY: str = os.getenv("HUGGING_FACE_KEY")
  HUGGING_FACE_MODEL: str = os.getenv("HUGGING_FACE_MODEL")

settings = Settings()