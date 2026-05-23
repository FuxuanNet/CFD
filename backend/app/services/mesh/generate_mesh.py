from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import gmsh

from app.core.workspace import read_json, require_file, workspace_api_path, write_json
from app.schemas.common import FileReference
from app.schemas.mesh import MeshGenerateRequest, MeshResponse
from app.services.cae_files import geometry_dir, mesh_dir
from app.services.geometry.gmsh_helpers import run_gmsh
from app.services.mesh.mesh_helpers import extract_mesh_metadata_from_inp, write_mesh_preview_from_gmsh_with_node_ids


ProgressCallback = Callable[[str, int, str, str], None]


@dataclass(frozen=True)
class MeshAttempt:
    name: str
    heal: bool
    dimension: int


def _noop_progress(_phase: str, _progress: int, _message: str, _channel: str = "mesh") -> None:
    return None


def _configure_mesh_size(mesh_size: float) -> None:
    gmsh.option.setNumber("Mesh.CharacteristicLengthMin", mesh_size)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", mesh_size)


def _heal_imported_geometry(make_solids: bool) -> None:
    gmsh.model.occ.healShapes(
        [],
        tolerance=1e-8,
        fixDegenerated=True,
        fixSmallEdges=True,
        fixSmallFaces=True,
        sewFaces=True,
        makeSolids=make_solids,
    )
    gmsh.model.occ.removeAllDuplicates()


def _prepare_model(step_path: Path, attempt: MeshAttempt, mesh_size: float) -> None:
    gmsh.clear()
    gmsh.model.add("step_mesh")
    gmsh.model.occ.importShapes(str(step_path))
    if attempt.heal:
        _heal_imported_geometry(make_solids=attempt.dimension == 3)
    gmsh.model.occ.synchronize()
    _configure_mesh_size(mesh_size)


def _generate_volume_mesh() -> None:
    volumes = gmsh.model.getEntities(3)
    if not volumes:
        raise RuntimeError("No solid volume found.")
    gmsh.model.addPhysicalGroup(3, [tag for _, tag in volumes], tag=1)
    gmsh.model.setPhysicalName(3, 1, "Volume")
    gmsh.model.mesh.generate(3)


def _generate_surface_mesh() -> None:
    surfaces = gmsh.model.getEntities(2)
    if not surfaces:
        raise RuntimeError("No displayable surface found.")
    gmsh.model.addPhysicalGroup(2, [tag for _, tag in surfaces], tag=1)
    gmsh.model.setPhysicalName(2, 1, "Surface")
    gmsh.model.mesh.generate(2)


def _write_mesh_log(mesh_log_path: Path, messages: list[str]) -> None:
    mesh_log_path.parent.mkdir(parents=True, exist_ok=True)
    mesh_log_path.write_text("\n".join(messages).rstrip() + "\n", encoding="utf-8")


def generate_mesh(request: MeshGenerateRequest, progress: ProgressCallback | None = None) -> MeshResponse:
    """Generate a finite element mesh for a geometry."""

    emit = progress or _noop_progress
    mesh_id = request.geometry_id
    step_path = require_file(geometry_dir(request.geometry_id) / "geometry.step", "Geometry STEP file not found.")
    geometry_metadata = read_json(geometry_dir(request.geometry_id) / "geometry.json")
    out_dir = mesh_dir(mesh_id)
    msh_path = out_dir / "mesh.msh"
    inp_path = out_dir / "mesh.inp"
    preview_path = out_dir / "mesh_preview.vtp"
    mesh_sets_path = out_dir / "mesh_sets.json"
    mesh_log_path = out_dir / "mesh.log"

    attempts = [
        MeshAttempt("raw volume mesh", heal=False, dimension=3),
        MeshAttempt("healed volume mesh", heal=True, dimension=3),
        MeshAttempt("raw surface mesh", heal=False, dimension=2),
        MeshAttempt("healed surface mesh", heal=True, dimension=2),
    ]
    errors: list[str] = []
    log_messages: list[str] = []
    chosen_attempt: MeshAttempt | None = None

    def log(message: str, phase: str = "mesh", progress_value: int = 20) -> None:
        log_messages.append(message)
        emit(phase, progress_value, message, "mesh")

    def task() -> None:
        nonlocal chosen_attempt
        total = len(attempts)
        for index, attempt in enumerate(attempts, start=1):
            base_progress = 10 + int((index - 1) * 60 / total)
            log(f"Attempt {index}/{total}: {attempt.name}.", "mesh_prepare", base_progress)
            try:
                _prepare_model(step_path, attempt, request.mesh_size)
                if attempt.dimension == 3:
                    _generate_volume_mesh()
                else:
                    _generate_surface_mesh()
                chosen_attempt = attempt
                log(f"Attempt succeeded: {attempt.name}.", "mesh_generate", min(base_progress + 12, 78))
                gmsh.write(str(msh_path))
                gmsh.write(str(inp_path))
                log("Gmsh MSH and CalculiX INP files written.", "mesh_write", 82)
                write_mesh_preview_from_gmsh_with_node_ids(inp_path, preview_path)
                log("Mesh preview VTP written with node_id point data.", "mesh_preview", 90)
                return
            except Exception as exc:
                message = f"{attempt.name} failed: {exc}"
                errors.append(message)
                log(message, "mesh_retry", min(base_progress + 8, 78))
        raise RuntimeError("Mesh generation failed after all strategies: " + " | ".join(errors))

    emit("mesh_start", 5, "Mesh generation started.", "message")
    try:
        run_gmsh(task)
    finally:
        _write_mesh_log(mesh_log_path, log_messages)

    if chosen_attempt is None:
        raise RuntimeError("Mesh generation did not select a mesh strategy.")

    analysis_ready = chosen_attempt.dimension == 3
    analysis_message = "" if analysis_ready else "STEP geometry did not form a solid volume for the current solver; surface mesh is available for display only."
    mesh_kind = "volume" if analysis_ready else "surface"
    mesh_sets = extract_mesh_metadata_from_inp(
        inp_path,
        mesh_kind=mesh_kind,
        analysis_ready=analysis_ready,
        analysis_message=analysis_message,
    )
    mesh_sets.update(
        {
            "mesh_id": mesh_id,
            "geometry_id": request.geometry_id,
            "mesh_size": request.mesh_size,
            "geometry_type": geometry_metadata.get("type"),
            "mesh_strategy": chosen_attempt.name,
            "mesh_log": workspace_api_path(mesh_log_path),
        }
    )
    write_json(mesh_sets_path, mesh_sets)
    emit("mesh_done", 100, "Mesh generation completed.", "message")

    return MeshResponse(
        message="Mesh generated." if analysis_ready else "Surface mesh generated; solid analysis is not available for this geometry.",
        mesh_id=mesh_id,
        geometry_id=request.geometry_id,
        mesh_kind=mesh_kind,
        analysis_ready=analysis_ready,
        analysis_message=analysis_message,
        files=[
            FileReference(name="mesh.msh", path=workspace_api_path(msh_path), description="Gmsh mesh file."),
            FileReference(name="mesh.inp", path=workspace_api_path(inp_path), description="Initial CalculiX/Abaqus-style mesh input."),
            FileReference(name="mesh_preview.vtp", path=workspace_api_path(preview_path), description="Surface mesh preview for frontend."),
            FileReference(name="mesh_sets.json", path=workspace_api_path(mesh_sets_path), description="Mesh node IDs and analysis readiness metadata."),
            FileReference(name="mesh.log", path=workspace_api_path(mesh_log_path), description="Mesh generation attempt log."),
        ],
    )
