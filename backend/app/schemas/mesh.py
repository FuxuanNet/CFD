from pydantic import BaseModel, Field

from app.schemas.common import FileReference


class MeshGenerateRequest(BaseModel):
    geometry_id: str = Field(..., min_length=1)
    mesh_size: float = Field(..., gt=0, description="Global mesh size in mm.")


class MeshResponse(BaseModel):
    success: bool = True
    message: str
    mesh_id: str
    geometry_id: str
    mesh_kind: str = Field(default="volume", description="Generated mesh kind: volume or surface.")
    analysis_ready: bool = Field(default=True, description="Whether the mesh can be used by the current solid solver.")
    analysis_message: str = Field(default="", description="Reason when analysis_ready is false.")
    files: list[FileReference]
