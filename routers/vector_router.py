## webhook 받아서 벡터화 하는 처리
from fastapi import APIRouter, Depends

from database import get_db
from schemas.vector_dto import VectorCreateResponse, VectorCreateRequest
from sqlalchemy.orm import Session
from services.vector_service import VectorService


router=APIRouter(prefix="/vector",tags=["vector"])

@router.post("/", response_model=VectorCreateResponse)
async def create_vector(req: VectorCreateRequest, db: Session = Depends(get_db)):
    svc = VectorService()

    try:
        doc_id = await svc.create_vector(
            db=db,
            title=req.title,
            html=req.html,
            metadata=req.metadata,
        )
        return VectorCreateResponse(
            doc_id=str(doc_id),
            message="Vector created successfully"
        )

    except Exception as e:
        print(f"[Vector Router Error] {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))