from fastapi import APIRouter
from models.query import QueryRequest
from services.query_service import process_query

router=APIRouter(
    prefix="/api/v1",
    tags=["Query"]
)

@router.post("/query")
def query_company_brain(request: QueryRequest):
    return process_query(request.question)