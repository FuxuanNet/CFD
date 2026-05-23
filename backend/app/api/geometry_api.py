from fastapi import APIRouter, File, UploadFile

from app.api.error_handling import as_http_error
from app.schemas.geometry import BoxGeometryRequest, CylinderGeometryRequest, GeometryResponse, SphereGeometryRequest
from app.services.geometry.create_box_geometry import create_box_geometry
from app.services.geometry.create_primitive_geometry import create_cylinder_geometry, create_sphere_geometry
from app.services.geometry.import_step_geometry import import_step_geometry

router = APIRouter(prefix="/geometry", tags=["geometry"])


@router.post("/box", response_model=GeometryResponse)
def create_box(request: BoxGeometryRequest) -> GeometryResponse:
    return as_http_error("geometry generation", lambda: create_box_geometry(request))


@router.post("/sphere", response_model=GeometryResponse)
def create_sphere(request: SphereGeometryRequest) -> GeometryResponse:
    return as_http_error("sphere generation", lambda: create_sphere_geometry(request))


@router.post("/cylinder", response_model=GeometryResponse)
def create_cylinder(request: CylinderGeometryRequest) -> GeometryResponse:
    return as_http_error("cylinder generation", lambda: create_cylinder_geometry(request))


@router.post("/step", response_model=GeometryResponse)
def import_step(file: UploadFile = File(...)) -> GeometryResponse:
    return as_http_error("geometry import", lambda: import_step_geometry(file))
