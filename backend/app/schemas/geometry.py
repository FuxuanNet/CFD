from pydantic import BaseModel, Field

from app.schemas.common import FileReference


class BoxGeometryRequest(BaseModel):
    length: float = Field(..., gt=0, description="Beam length along X axis, in mm.")
    width: float = Field(..., gt=0, description="Beam width along Y axis, in mm.")
    height: float = Field(..., gt=0, description="Beam height along Z axis, in mm.")


class SphereGeometryRequest(BaseModel):
    radius: float = Field(..., gt=0, description="Sphere radius in mm.")


class CylinderGeometryRequest(BaseModel):
    radius: float = Field(..., gt=0, description="Cylinder radius in mm.")
    height: float = Field(..., gt=0, description="Cylinder height along Z axis, in mm.")


class GeometryResponse(BaseModel):
    success: bool = True
    message: str
    geometry_id: str
    files: list[FileReference]
