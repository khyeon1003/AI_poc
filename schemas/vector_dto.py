from pydantic import BaseModel

class VectorCreateRequest(BaseModel):
  title: str
  html: str
  metadata: dict = {}


# ---- Response Schema ----
class VectorCreateResponse(BaseModel):
  doc_id: str
  message: str