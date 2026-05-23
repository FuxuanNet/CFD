import gmsh

from app.core.workspace import new_job_id, workspace_api_path, write_json
from app.schemas.common import FileReference
from app.schemas.geometry import BoxGeometryRequest, GeometryResponse
from app.services.cae_files import geometry_dir
from app.services.geometry.gmsh_helpers import run_gmsh, write_box_preview


def create_box_geometry(request: BoxGeometryRequest) -> GeometryResponse:
    """Create a box beam geometry from dimensions.

    Input:
        length, width, height in mm.

    Return:
        Geometry ID plus placeholder STEP, preview VTP, and metadata paths.

    This implementation writes real STEP, VTP preview, and metadata files.
    """

    geometry_id = new_job_id()
    out_dir = geometry_dir(geometry_id)
    step_path = out_dir / "geometry.step"
    preview_path = out_dir / "geometry_preview.vtp"
    metadata_path = out_dir / "geometry.json"

    def task() -> None:
        gmsh.model.add("box_beam")
        gmsh.model.occ.addBox(0, 0, 0, request.length, request.width, request.height)
        gmsh.model.occ.synchronize()
        gmsh.write(str(step_path))

    run_gmsh(task)
    write_box_preview(preview_path, request.length, request.width, request.height)
    write_json(
        metadata_path,
        {
            "geometry_id": geometry_id,
            "type": "box",
            "length": request.length,
            "width": request.width,
            "height": request.height,
            "unit": "mm",
        },
    )

    return GeometryResponse(
        message="Box geometry created.",
        geometry_id=geometry_id,
        files=[
            FileReference(name="geometry.step", path=workspace_api_path(step_path), description="STEP geometry file."),
            FileReference(name="geometry_preview.vtp", path=workspace_api_path(preview_path), description="Surface preview for frontend."),
            FileReference(name="geometry.json", path=workspace_api_path(metadata_path), description="Geometry metadata and input dimensions."),
        ],
    )
