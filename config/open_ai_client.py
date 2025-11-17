from openai import OpenAI
from .config import settings

open_ai_client = OpenAI(
    api_key=settings.OPENAI_API_KEY,
)