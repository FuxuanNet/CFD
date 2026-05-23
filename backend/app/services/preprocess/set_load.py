from app.core.workspace import read_json, require_file, workspace_api_path, write_json
from app.schemas.common import FileReference
from app.schemas.preprocess import LoadItem, LoadRequest, LoadResponse
from app.services.cae_files import mesh_dir, preprocess_dir
from app.services.mesh.mesh_helpers import validate_node_ids


def _normalize_load_items(request: LoadRequest) -> list[LoadItem]:
    if request.loads is not None:
        if not request.loads:
            raise ValueError("At least one load item is required.")
        return request.loads
    if not request.node_ids:
        raise ValueError("Load node selection is empty.")
    return [
        LoadItem(
            id="load_1",
            name="F1",
            node_ids=request.node_ids,
            direction=request.direction,
            magnitude=request.magnitude,
        )
    ]


def set_load(request: LoadRequest) -> LoadResponse:
    """Store one or more load settings for the current mesh node selections."""

    load_id = request.mesh_id
    load_path = preprocess_dir(request.mesh_id) / "load.json"
    mesh_sets_path = require_file(mesh_dir(request.mesh_id) / "mesh_sets.json", "Mesh node sets file not found.")
    mesh_sets = read_json(mesh_sets_path)
    if not mesh_sets.get("analysis_ready"):
        raise ValueError(mesh_sets.get("analysis_message") or "Current mesh is not ready for solid analysis.")

    loads = []
    for index, item in enumerate(_normalize_load_items(request), start=1):
        node_ids = validate_node_ids(mesh_sets, item.node_ids)
        direction = item.direction.lower()
        if direction not in {"x", "y", "z"}:
            raise ValueError(f"Unsupported load direction: {item.direction}")
        loads.append(
            {
                "id": item.id or f"load_{index}",
                "name": item.name or f"F{index}",
                "node_ids": node_ids,
                "direction": direction,
                "magnitude": item.magnitude,
                "unit": "N",
                "node_count": len(node_ids),
            }
        )

    first_load = loads[0]
    write_json(
        load_path,
        {
            "load_id": load_id,
            "mesh_id": request.mesh_id,
            "loads": loads,
            "load_count": len(loads),
            "unit": "N",
            # Legacy fields keep old readers/tests compatible while the solver uses loads[].
            "node_ids": first_load["node_ids"],
            "direction": first_load["direction"],
            "magnitude": first_load["magnitude"],
            "node_count": first_load["node_count"],
        },
    )

    return LoadResponse(
        message="Load saved.",
        load_id=load_id,
        mesh_id=request.mesh_id,
        load_count=len(loads),
        files=[
            FileReference(name="load.json", path=workspace_api_path(load_path), description="Load node selection, direction, and magnitude."),
        ],
    )
