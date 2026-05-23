from __future__ import annotations

from pathlib import Path

import gmsh
import numpy as np
import pyvista as pv
from scipy.spatial import cKDTree


def _node_ids_from_inp(mesh_inp_path: Path) -> dict[int, tuple[float, float, float]]:
    nodes: dict[int, tuple[float, float, float]] = {}
    in_node_block = False
    for raw_line in mesh_inp_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("*"):
            in_node_block = line.upper().startswith("*NODE")
            continue
        if in_node_block:
            parts = [part.strip() for part in line.split(",")]
            if len(parts) >= 4:
                nodes[int(parts[0])] = (float(parts[1]), float(parts[2]), float(parts[3]))
    if not nodes:
        raise ValueError(f"No nodes found in {mesh_inp_path}")
    return nodes


def _attach_node_ids(surface: pv.PolyData, nodes: dict[int, tuple[float, float, float]]) -> pv.PolyData:
    if surface.n_points == 0:
        raise ValueError("Surface preview mesh is empty.")
    node_items = sorted(nodes.items())
    coords = np.array([xyz for _node_id, xyz in node_items])
    ids = np.array([node_id for node_id, _xyz in node_items], dtype=np.int64)
    surface_points = np.asarray(surface.points)
    _distances, indices = cKDTree(coords).query(surface_points)
    node_ids = ids[indices]
    surface.point_data["node_id"] = node_ids
    return surface


def _surface_from_gmsh() -> pv.PolyData:
    node_tags, coords, _params = gmsh.model.mesh.getNodes(-1, -1, True, False)
    if len(node_tags) == 0:
        raise ValueError("Mesh preview has no nodes.")

    points = np.asarray(coords, dtype=float).reshape(-1, 3)
    node_index = {int(tag): index for index, tag in enumerate(node_tags)}
    faces: list[int] = []
    element_types, _element_tags, element_node_tags = gmsh.model.mesh.getElements(2)
    for element_type, flat_node_tags in zip(element_types, element_node_tags):
        _name, element_dim, _order, node_count, _local_coords, _primary_nodes = gmsh.model.mesh.getElementProperties(element_type)
        if element_dim != 2 or node_count < 3:
            continue
        nodes = np.asarray(flat_node_tags, dtype=np.int64).reshape(-1, node_count)
        for element_nodes in nodes:
            try:
                point_ids = [node_index[int(tag)] for tag in element_nodes]
            except KeyError as exc:
                raise ValueError(f"Mesh preview element references missing node {exc.args[0]}.") from exc
            faces.extend([node_count, *point_ids])

    if not faces:
        raise ValueError("Mesh preview has no surface elements.")
    surface = pv.PolyData(points, np.asarray(faces, dtype=np.int64))
    if surface.n_points == 0 or surface.n_cells == 0:
        raise ValueError("Mesh preview is empty.")
    return surface


def write_mesh_preview_from_gmsh_with_node_ids(inp_path: Path, preview_path: Path) -> None:
    """Write the current Gmsh surface mesh as VTP and attach CalculiX node IDs."""

    preview_path.parent.mkdir(parents=True, exist_ok=True)
    surface = _surface_from_gmsh()
    nodes = _node_ids_from_inp(inp_path)
    _attach_node_ids(surface, nodes)
    surface.save(preview_path)


def read_preview_node_ids(preview_path: Path) -> list[int]:
    """Read node_id point data from a VTP preview for tests and diagnostics."""

    surface = pv.read(preview_path)
    if "node_id" not in surface.point_data:
        return []
    return [int(value) for value in np.asarray(surface.point_data["node_id"]).reshape(-1)]


def extract_mesh_metadata_from_inp(mesh_inp_path: Path, mesh_kind: str, analysis_ready: bool, analysis_message: str = "") -> dict[str, object]:
    """Extract node metadata from an Abaqus/CalculiX mesh INP file."""

    nodes = _node_ids_from_inp(mesh_inp_path)
    coords = np.array(list(nodes.values()))
    node_ids = sorted(nodes)

    return {
        "bounds": {
            "xmin": float(coords[:, 0].min()),
            "xmax": float(coords[:, 0].max()),
            "ymin": float(coords[:, 1].min()),
            "ymax": float(coords[:, 1].max()),
            "zmin": float(coords[:, 2].min()),
            "zmax": float(coords[:, 2].max()),
        },
        "mesh_kind": mesh_kind,
        "analysis_ready": analysis_ready,
        "analysis_message": analysis_message,
        "node_ids": node_ids,
        "selectable_node_ids": node_ids,
        "node_count": len(nodes),
    }


def validate_node_ids(mesh_sets: dict[str, object], node_ids: list[int]) -> list[int]:
    """Return unique selected node IDs after checking they belong to the mesh."""

    selected = sorted({int(node_id) for node_id in node_ids})
    if not selected:
        raise ValueError("Node selection is empty.")
    valid = {int(node_id) for node_id in mesh_sets.get("node_ids", [])}
    missing = [node_id for node_id in selected if node_id not in valid]
    if missing:
        preview = ", ".join(str(node_id) for node_id in missing[:8])
        suffix = "..." if len(missing) > 8 else ""
        raise ValueError(f"Selected node IDs are not in the mesh: {preview}{suffix}")
    return selected
