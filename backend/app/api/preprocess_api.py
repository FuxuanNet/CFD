from fastapi import APIRouter

from app.api.error_handling import as_http_error
from app.schemas.preprocess import (
    BoundaryRequest,
    BoundaryResponse,
    LoadRequest,
    LoadResponse,
    MaterialRequest,
    MaterialResponse,
)
from app.services.preprocess.set_boundary import set_boundary
from app.services.preprocess.set_load import set_load
from app.services.preprocess.set_material import set_material

router = APIRouter(prefix="/preprocess", tags=["preprocess"])


@router.post("/material", response_model=MaterialResponse)
def material(request: MaterialRequest) -> MaterialResponse:
    return as_http_error("material setup", lambda: set_material(request))


@router.post("/boundary", response_model=BoundaryResponse)
def boundary(request: BoundaryRequest) -> BoundaryResponse:
    return as_http_error("boundary setup", lambda: set_boundary(request))


@router.post("/load", response_model=LoadResponse)
def load(request: LoadRequest) -> LoadResponse:
    return as_http_error("load setup", lambda: set_load(request))
