from pydantic import BaseModel, Field

from app.schemas.common import FileReference


class MaterialRequest(BaseModel):
    mesh_id: str = Field(..., min_length=1)
    name: str = Field(default="Steel", min_length=1)
    elastic_modulus: float = Field(default=210000.0, gt=0, description="Elastic modulus in MPa.")
    poisson_ratio: float = Field(default=0.3, gt=0, lt=0.5)


class BoundaryRequest(BaseModel):
    mesh_id: str = Field(..., min_length=1)
    node_ids: list[int] = Field(..., min_length=1, description="Selected CalculiX node IDs to fix.")
    dofs: list[int] = Field(default=[1, 2, 3], min_length=1, max_length=3, description="Constrained DOFs.")


class LoadItem(BaseModel):
    id: str | None = Field(default=None, description="Client-side load item ID.")
    name: str | None = Field(default=None, description="Human readable load name.")
    node_ids: list[int] = Field(..., description="Selected CalculiX node IDs to load.")
    direction: str = Field(default="z", description="Load direction axis.")
    magnitude: float = Field(default=-1000.0, description="Total load magnitude in N.")


class LoadRequest(BaseModel):
    mesh_id: str = Field(..., min_length=1)
    loads: list[LoadItem] | None = Field(default=None, description="Multiple force items in one static step.")
    node_ids: list[int] | None = Field(default=None, description="Legacy single load node IDs.")
    direction: str = Field(default="z", description="Legacy single load direction axis.")
    magnitude: float = Field(default=-1000.0, description="Legacy single load magnitude in N.")


class MaterialResponse(BaseModel):
    success: bool = True
    message: str
    material_id: str
    mesh_id: str
    files: list[FileReference]


class BoundaryResponse(BaseModel):
    success: bool = True
    message: str
    boundary_id: str
    mesh_id: str
    files: list[FileReference]


class LoadResponse(BaseModel):
    success: bool = True
    message: str
    load_id: str
    mesh_id: str
    load_count: int = 1
    files: list[FileReference]
