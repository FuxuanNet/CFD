from __future__ import annotations

import re
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.core.workspace import workspace_root


router = APIRouter(prefix="/files", tags=["files"])

JOB_ID_PATTERN = re.compile(r"^job_[0-9a-f]{12}$")

ALLOWED_FILES_BY_STAGE: dict[str, set[str]] = {
    "geometry": {"geometry.step", "geometry_preview.vtp", "geometry.json"},
    "mesh": {"mesh.msh", "mesh.inp", "mesh_preview.vtp", "mesh_sets.json", "mesh.log"},
    "preprocess": {"material.json", "boundary.json", "load.json"},
    "solver": {"model.inp", "model.frd", "model.dat", "solver.log"},
    "results": {
        "result.vtu",
        "result_surface_displacement.vtp",
        "result_surface_von_mises.vtp",
        "result_summary.json",
    },
}


def _is_plain_filename(filename: str) -> bool:
    return filename == Path(filename).name and "/" not in filename and "\\" not in filename and filename not in {".", ".."}


def resolve_workspace_file(job_id: str, stage: str, filename: str) -> Path:
    """Resolve a whitelisted workspace artifact without exposing arbitrary paths."""

    if not JOB_ID_PATTERN.fullmatch(job_id):
        raise HTTPException(status_code=400, detail="Invalid job_id.")
    if stage not in ALLOWED_FILES_BY_STAGE:
        raise HTTPException(status_code=400, detail="Invalid workspace stage.")
    if not _is_plain_filename(filename):
        raise HTTPException(status_code=400, detail="Invalid filename.")
    if filename not in ALLOWED_FILES_BY_STAGE[stage]:
        raise HTTPException(status_code=400, detail="File is not exposed by the files API.")

    root = workspace_root().resolve()
    file_path = (root / job_id / stage / filename).resolve()
    try:
        file_path.relative_to(root)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Resolved path escapes workspace.") from exc
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Workspace file not found.")
    return file_path


@router.get("/{job_id}/{stage}/{filename}")
def get_workspace_file(job_id: str, stage: str, filename: str) -> FileResponse:
    file_path = resolve_workspace_file(job_id, stage, filename)
    return FileResponse(file_path, filename=file_path.name)
