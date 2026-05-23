from __future__ import annotations

from pathlib import Path
from typing import Callable, TypeVar

import gmsh
import numpy as np
import pyvista as pv


T = TypeVar("T")


def run_gmsh(task: Callable[[], T]) -> T:
    """Run a Gmsh task with a clean initialize/finalize lifecycle."""

    gmsh.initialize(interruptible=False)
    gmsh.option.setNumber("General.Terminal", 0)
    try:
        return task()
    finally:
        gmsh.finalize()


def write_box_preview(path: Path, length: float, width: float, height: float) -> None:
    """Write a simple VTP surface preview for a box beam."""

    path.parent.mkdir(parents=True, exist_ok=True)
    grid = pv.Box(bounds=(0.0, length, 0.0, width, 0.0, height))
    grid.save(path)


def write_step_preview(step_path: Path, preview_path: Path) -> None:
    """Write a real surface preview for imported STEP geometry."""

    def write_surface_from_gmsh() -> None:
        node_tags, coords, _params = gmsh.model.mesh.getNodes(-1, -1, True, False)
        if len(node_tags) == 0:
            raise RuntimeError("STEP surface preview has no mesh nodes.")

        points = np.asarray(coords, dtype=float).reshape(-1, 3)
        node_index = {int(tag): index for index, tag in enumerate(node_tags)}
        faces: list[int] = []

        element_types, _element_tags, element_node_tags = gmsh.model.mesh.getElements(2)
        for element_type, flat_node_tags in zip(element_types, element_node_tags):
            element_name, element_dim, _order, node_count, _local_coords, _primary_nodes = gmsh.model.mesh.getElementProperties(element_type)
            if element_dim != 2 or node_count < 3:
                continue
            nodes = np.asarray(flat_node_tags, dtype=np.int64).reshape(-1, node_count)
            for element_nodes in nodes:
                try:
                    point_ids = [node_index[int(tag)] for tag in element_nodes]
                except KeyError as exc:
                    raise RuntimeError(f"STEP preview element references missing node {exc.args[0]}.") from exc
                faces.extend([node_count, *point_ids])

        if not faces:
            raise RuntimeError("STEP surface preview mesh is empty.")

        preview_path.parent.mkdir(parents=True, exist_ok=True)
        surface = pv.PolyData(points, np.asarray(faces, dtype=np.int64))
        if surface.n_cells == 0 or surface.n_points == 0:
            raise RuntimeError("STEP surface preview mesh is empty.")
        surface.save(preview_path)

    def generate_surface_preview(heal: bool) -> None:
        if heal:
            gmsh.model.occ.healShapes(
                [],
                tolerance=1e-8,
                fixDegenerated=True,
                fixSmallEdges=True,
                fixSmallFaces=True,
                sewFaces=True,
                makeSolids=False,
            )
            gmsh.model.occ.removeAllDuplicates()
        gmsh.model.occ.synchronize()
        surfaces = gmsh.model.getEntities(2)
        if not surfaces:
            raise RuntimeError("No displayable surface found in STEP geometry.")
        gmsh.model.mesh.generate(2)
        write_surface_from_gmsh()

    def task() -> None:
        errors: list[str] = []
        for heal in (False, True):
            gmsh.clear()
            gmsh.model.add("step_preview")
            gmsh.model.occ.importShapes(str(step_path))
            try:
                generate_surface_preview(heal)
                return
            except Exception as exc:
                errors.append(str(exc))
        raise RuntimeError("STEP surface preview failed: " + " | ".join(message for message in errors if message))

    run_gmsh(task)
