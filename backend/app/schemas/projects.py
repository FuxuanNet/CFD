from typing import Any

from pydantic import BaseModel, Field


class ProjectCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)


class ProjectUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    case_id: str | None = Field(default=None)
    snapshot: dict[str, Any] | None = None


class ProjectResponse(BaseModel):
    success: bool = True
    project_id: str
    name: str
    case_id: str | None = None
    created_at: str
    updated_at: str


class ProjectListResponse(BaseModel):
    success: bool = True
    projects: list[ProjectResponse]


class ProjectSnapshotResponse(BaseModel):
    success: bool = True
    project: ProjectResponse
    snapshot: dict[str, Any]


class ProjectDeleteResponse(BaseModel):
    success: bool = True
    message: str
    project_id: str
