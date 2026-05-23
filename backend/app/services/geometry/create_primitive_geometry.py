from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import gmsh

from app.core.workspace import new_job_id, workspace_api_path, write_json
from app.schemas.common import FileReference
from app.schemas.geometry import CylinderGeometryRequest, GeometryResponse, SphereGeometryRequest
from app.services.cae_files import geometry_dir
from app.services.geometry.gmsh_helpers import run_gmsh, write_step_preview


def _primitive_response(
    *,
    geometry_id: str,
    message: str,
    step_path: Path,
    preview_path: Path,
    metadata_path: Path,
) -> GeometryResponse:
    return GeometryResponse(
        message=message,
        geometry_id=geometry_id,
        files=[
            FileReference(name="geometry.step", path=workspace_api_path(step_path), description="STEP geometry file."),
            FileReference(name="geometry_preview.vtp", path=workspace_api_path(preview_path), description="Surface preview for frontend."),
            FileReference(name="geometry.json", path=workspace_api_path(metadata_path), description="Geometry metadata and input dimensions."),
        ],
    )


def _write_occ_primitive(
    *,
    model_name: str,
    metadata: dict[str, Any],
    build_shape: Callable[[], None],
    message: str,
) -> GeometryResponse:
    geometry_id = new_job_id()
    out_dir = geometry_dir(geometry_id)
    step_path = out_dir / "geometry.step"
    preview_path = out_dir / "geometry_preview.vtp"
    metadata_path = out_dir / "geometry.json"

    def task() -> None:
        gmsh.model.add(model_name)
        build_shape()
        gmsh.model.occ.synchronize()
        gmsh.write(str(step_path))

    run_gmsh(task)
    write_step_preview(step_path, preview_path)
    write_json(metadata_path, {"geometry_id": geometry_id, **metadata, "unit": "mm"})
    return _primitive_response(
        geometry_id=geometry_id,
        message=message,
        step_path=step_path,
        preview_path=preview_path,
        metadata_path=metadata_path,
    )


def create_sphere_geometry(request: SphereGeometryRequest) -> GeometryResponse:
    return _write_occ_primitive(
        model_name="sphere",
        metadata={"type": "sphere", "radius": request.radius},
        build_shape=lambda: gmsh.model.occ.addSphere(0, 0, 0, request.radius),
        message="Sphere geometry created.",
    )


def create_cylinder_geometry(request: CylinderGeometryRequest) -> GeometryResponse:
    return _write_occ_primitive(
        model_name="cylinder",
        metadata={"type": "cylinder", "radius": request.radius, "height": request.height},
        build_shape=lambda: gmsh.model.occ.addCylinder(0, 0, 0, 0, 0, request.height, request.radius),
        message="Cylinder geometry created.",
    )
