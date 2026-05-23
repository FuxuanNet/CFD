from app.core.workspace import read_json, require_file, workspace_api_path, write_json
from app.schemas.common import FileReference
from app.schemas.preprocess import BoundaryRequest, BoundaryResponse
from app.services.cae_files import mesh_dir, preprocess_dir
from app.services.mesh.mesh_helpers import validate_node_ids


def set_boundary(request: BoundaryRequest) -> BoundaryResponse:
    """Store fixed node set settings for the current mesh."""

    boundary_id = request.mesh_id
    boundary_path = preprocess_dir(request.mesh_id) / "boundary.json"
    mesh_sets_path = require_file(mesh_dir(request.mesh_id) / "mesh_sets.json", "Mesh node sets file not found.")
    mesh_sets = read_json(mesh_sets_path)
    if not mesh_sets.get("analysis_ready"):
        raise ValueError(mesh_sets.get("analysis_message") or "Current mesh is not ready for solid analysis.")
    node_ids = validate_node_ids(mesh_sets, request.node_ids)
    dofs = sorted({int(dof) for dof in request.dofs})
    unsupported = [dof for dof in dofs if dof not in {1, 2, 3}]
    if unsupported:
        raise ValueError(f"Unsupported constrained DOFs: {unsupported}")
    write_json(
        boundary_path,
        {
            "boundary_id": boundary_id,
            "mesh_id": request.mesh_id,
            "node_ids": node_ids,
            "type": "fixed",
            "dofs": dofs,
            "node_count": len(node_ids),
        },
    )

    return BoundaryResponse(
        message="Boundary saved.",
        boundary_id=boundary_id,
        mesh_id=request.mesh_id,
        files=[
            FileReference(name="boundary.json", path=workspace_api_path(boundary_path), description="Fixed node selection and constrained DOFs."),
        ],
    )
