from pydantic import BaseModel

class RagasChatRequest(BaseModel):
    question: str
    conversation_id: str