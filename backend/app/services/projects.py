from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.workspace import clean_job, read_json, workspace_root, write_json
from app.schemas.projects import (
    ProjectCreateRequest,
    ProjectDeleteResponse,
    ProjectListResponse,
    ProjectResponse,
    ProjectSnapshotResponse,
    ProjectUpdateRequest,
)
from app.services._ids import make_id


PROJECT_INDEX_FILE = "projects.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _index_path() -> Path:
    return workspace_root() / PROJECT_INDEX_FILE


def _empty_snapshot() -> dict[str, Any]:
    return {
        "state": {},
        "forms": {},
        "selection": {},
        "files": [],
        "logs": [],
        "view": {},
    }


def _load_index() -> dict[str, Any]:
    path = _index_path()
    if not path.exists():
        return {"projects": []}
    data = read_json(path)
    if "projects" not in data or not isinstance(data["projects"], list):
        return {"projects": []}
    return data


def _save_index(data: dict[str, Any]) -> None:
    write_json(_index_path(), data)


def _normalize_name(name: str) -> str:
    normalized = " ".join(name.strip().split())
    if not normalized:
        raise ValueError("Project name cannot be empty.")
    return normalized


def _assert_unique_name(projects: list[dict[str, Any]], name: str, project_id: str | None = None) -> None:
    lowered = name.casefold()
    for project in projects:
        if project_id and project.get("project_id") == project_id:
            continue
        if str(project.get("name", "")).casefold() == lowered:
            raise ValueError("Project name already exists.")


def _find_project(projects: list[dict[str, Any]], project_id: str) -> dict[str, Any]:
    for project in projects:
        if project.get("project_id") == project_id:
            return project
    raise FileNotFoundError("Project not found.")


def _project_response(project: dict[str, Any]) -> ProjectResponse:
    return ProjectResponse(
        project_id=project["project_id"],
        name=project["name"],
        case_id=project.get("case_id"),
        created_at=project["created_at"],
        updated_at=project["updated_at"],
    )


def list_projects() -> ProjectListResponse:
    data = _load_index()
    projects = sorted(data["projects"], key=lambda item: item.get("updated_at", ""), reverse=True)
    return ProjectListResponse(projects=[_project_response(project) for project in projects])


def create_project(request: ProjectCreateRequest) -> ProjectResponse:
    data = _load_index()
    name = _normalize_name(request.name)
    _assert_unique_name(data["projects"], name)
    timestamp = _now()
    project = {
        "project_id": make_id("project"),
        "name": name,
        "case_id": None,
        "snapshot": _empty_snapshot(),
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    data["projects"].append(project)
    _save_index(data)
    return _project_response(project)


def update_project(project_id: str, request: ProjectUpdateRequest) -> ProjectResponse:
    data = _load_index()
    project = _find_project(data["projects"], project_id)
    if request.name is not None:
        name = _normalize_name(request.name)
        _assert_unique_name(data["projects"], name, project_id)
        project["name"] = name
    if request.case_id is not None:
        project["case_id"] = request.case_id or None
    if request.snapshot is not None:
        project["snapshot"] = request.snapshot
    project["updated_at"] = _now()
    _save_index(data)
    return _project_response(project)


def get_project_snapshot(project_id: str) -> ProjectSnapshotResponse:
    data = _load_index()
    project = _find_project(data["projects"], project_id)
    snapshot = project.get("snapshot")
    if not isinstance(snapshot, dict):
        snapshot = _empty_snapshot()
    return ProjectSnapshotResponse(project=_project_response(project), snapshot=snapshot)


def delete_project(project_id: str) -> ProjectDeleteResponse:
    data = _load_index()
    project = _find_project(data["projects"], project_id)
    case_id = project.get("case_id")
    if case_id:
        clean_job(str(case_id))
    data["projects"] = [item for item in data["projects"] if item.get("project_id") != project_id]
    _save_index(data)
    return ProjectDeleteResponse(message="Project deleted.", project_id=project_id)
