from fastapi import APIRouter

from app.api.error_handling import as_http_error
from app.schemas.results import ResultFieldName, ResultFieldResponse, ResultSummaryResponse
from app.services.results.get_result_field import get_result_field
from app.services.results.get_result_summary import get_result_summary

router = APIRouter(prefix="/results", tags=["results"])


@router.get("/{result_id}/summary", response_model=ResultSummaryResponse)
def summary(result_id: str) -> ResultSummaryResponse:
    return as_http_error("result summary", lambda: get_result_summary(result_id))


@router.get("/{result_id}/field", response_model=ResultFieldResponse)
def field(result_id: str, field: ResultFieldName) -> ResultFieldResponse:
    return as_http_error("result field", lambda: get_result_field(result_id, field))
