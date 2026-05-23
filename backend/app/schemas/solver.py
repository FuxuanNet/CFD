from pydantic import BaseModel, Field

from app.schemas.common import FileReference


class SolverRunRequest(BaseModel):
    mesh_id: str = Field(..., min_length=1)
    material_id: str = Field(..., min_length=1)
    boundary_id: str = Field(..., min_length=1)
    load_id: str = Field(..., min_length=1)
    solver_plugin_id: str = Field(..., min_length=1)


class SolverPluginInfo(BaseModel):
    id: str
    name: str
    version: str


class SolverPluginListResponse(BaseModel):
    plugins: list[SolverPluginInfo]


class SolverRunResponse(BaseModel):
    success: bool = True
    message: str
    result_id: str
    status: str
    files: list[FileReference]

