from fastapi import APIRouter

from app.api.error_handling import as_http_error
from app.schemas.projects import (
    ProjectCreateRequest,
    ProjectDeleteResponse,
    ProjectListResponse,
    ProjectResponse,
    ProjectSnapshotResponse,
    ProjectUpdateRequest,
)
from app.services.projects import create_project, delete_project, get_project_snapshot, list_projects, update_project


router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=ProjectListResponse)
def list_all_projects() -> ProjectListResponse:
    return as_http_error("project list", list_projects)


@router.post("", response_model=ProjectResponse)
def create(request: ProjectCreateRequest) -> ProjectResponse:
    return as_http_error("project create", lambda: create_project(request))


@router.patch("/{project_id}", response_model=ProjectResponse)
def update(project_id: str, request: ProjectUpdateRequest) -> ProjectResponse:
    return as_http_error("project update", lambda: update_project(project_id, request))


@router.delete("/{project_id}", response_model=ProjectDeleteResponse)
def delete(project_id: str) -> ProjectDeleteResponse:
    return as_http_error("project delete", lambda: delete_project(project_id))


@router.get("/{project_id}/snapshot", response_model=ProjectSnapshotResponse)
def snapshot(project_id: str) -> ProjectSnapshotResponse:
    return as_http_error("project snapshot", lambda: get_project_snapshot(project_id))
