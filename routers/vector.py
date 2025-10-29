## webhook 받아서 벡터화 하는 처리
from fastapi import APIRouter

from services.VectorService import VectorService

router=APIRouter(prefix="vector",tags=["vector"])

@router.post("/")## res 추가?
async def create_vector(request: Request):
    try:
        return VectorService.create_vector()
    except Exception as e: