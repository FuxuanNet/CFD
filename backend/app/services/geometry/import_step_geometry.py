from fastapi import UploadFile

from app.core.workspace import new_job_id, workspace_api_path, write_json
from app.schemas.common import FileReference
from app.schemas.geometry import GeometryResponse
from app.services.cae_files import geometry_dir
from app.services.geometry.gmsh_helpers import write_step_preview


def import_step_geometry(file: UploadFile) -> GeometryResponse:
    """Register an uploaded STEP file as geometry input.

    Input:
        Multipart file field named `file`.

    Return:
        Geometry ID plus placeholder saved STEP and preview VTP paths.

    This implementation saves the uploaded file and writes a bounding-box preview.
    """

    geometry_id = new_job_id()
    out_dir = geometry_dir(geometry_id)
    step_path = out_dir / "geometry.step"
    preview_path = out_dir / "geometry_preview.vtp"
    metadata_path = out_dir / "geometry.json"
    original_name = file.filename or "uploaded.step"
    content = file.file.read()
    step_path.write_bytes(content)
    write_step_preview(step_path, preview_path)
    write_json(
        metadata_path,
        {
            "geometry_id": geometry_id,
            "type": "step",
            "original_name": original_name,
            "unit": "mm",
        },
    )

    return GeometryResponse(
        message="STEP geometry imported.",
        geometry_id=geometry_id,
        files=[
            FileReference(name=original_name, path=workspace_api_path(step_path), description="Uploaded STEP geometry file."),
            FileReference(name="geometry_preview.vtp", path=workspace_api_path(preview_path), description="Surface preview for frontend."),
            FileReference(name="geometry.json", path=workspace_api_path(metadata_path), description="Geometry metadata."),
        ],
    )
