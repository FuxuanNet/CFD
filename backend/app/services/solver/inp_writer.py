from __future__ import annotations

from pathlib import Path


def _format_id_list(ids: list[int], width: int = 16) -> list[str]:
    lines: list[str] = []
    for index in range(0, len(ids), width):
        lines.append(", ".join(str(value) for value in ids[index : index + width]))
    return lines


def _clean_mesh_inp(mesh_inp_path: Path) -> str:
    """Keep Gmsh mesh content and strip analysis blocks if they appear."""

    stop_keywords = ("*MATERIAL", "*BOUNDARY", "*CLOAD", "*STEP")
    lines: list[str] = []
    skipping_heading_data = False
    for raw_line in mesh_inp_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        stripped = raw_line.strip().upper()
        if skipping_heading_data:
            if not stripped.startswith("*"):
                continue
            skipping_heading_data = False
        if any(stripped.startswith(keyword) for keyword in stop_keywords):
            break
        if stripped.startswith("*HEADING"):
            lines.append("*Heading")
            lines.append("CAE demo model")
            skipping_heading_data = True
            continue
        lines.append(raw_line)
    return "\n".join(lines).rstrip() + "\n"


def _normalized_loads(load: dict[str, object]) -> list[dict[str, object]]:
    raw_loads = load.get("loads")
    if isinstance(raw_loads, list):
        loads = [item for item in raw_loads if isinstance(item, dict)]
    else:
        loads = [
            {
                "name": "F1",
                "node_ids": load.get("node_ids", []),
                "direction": load.get("direction", "z"),
                "magnitude": load.get("magnitude", -1000.0),
            }
        ]
    if not loads:
        raise ValueError("At least one load item is required.")
    return loads


def write_model_inp(
    mesh_inp_path: Path,
    model_inp_path: Path,
    mesh_sets: dict[str, object],
    material: dict[str, object],
    boundary: dict[str, object],
    load: dict[str, object],
) -> None:
    """Write a complete CalculiX static analysis input file."""

    if not mesh_sets.get("analysis_ready", True):
        raise ValueError(mesh_sets.get("analysis_message") or "Current mesh is not ready for solid analysis.")

    fixed_nodes = [int(node) for node in boundary.get("node_ids", [])]
    if not fixed_nodes:
        raise ValueError("Boundary node set is empty.")

    direction_map = {"x": 1, "y": 2, "z": 3}
    load_blocks: list[dict[str, object]] = []
    for index, load_item in enumerate(_normalized_loads(load), start=1):
        load_nodes = [int(node) for node in load_item.get("node_ids", [])]
        if not load_nodes:
            raise ValueError(f"Load node set {index} is empty.")
        load_direction = str(load_item.get("direction", "z")).lower()
        dof = direction_map.get(load_direction)
        if dof is None:
            raise ValueError(f"Unsupported load direction: {load_direction}")
        total_force = float(load_item.get("magnitude", -1000.0))
        load_blocks.append(
            {
                "set_name": f"LOAD_SELECTION_{index}",
                "nodes": load_nodes,
                "dof": dof,
                "nodal_force": total_force / len(load_nodes),
            }
        )

    boundary_dofs = sorted({int(value) for value in boundary.get("dofs", [1, 2, 3])})
    unsupported_dofs = [value for value in boundary_dofs if value not in {1, 2, 3}]
    if unsupported_dofs:
        raise ValueError(f"Unsupported constrained DOFs: {unsupported_dofs}")
    elastic_modulus = float(material.get("elastic_modulus", 210000.0))
    poisson_ratio = float(material.get("poisson_ratio", 0.3))
    material_name = str(material.get("name", "Steel"))

    text = _clean_mesh_inp(mesh_inp_path)
    text += "\n*NSET, NSET=FIXED_SELECTION\n"
    text += "\n".join(_format_id_list(fixed_nodes)) + "\n"
    for load_block in load_blocks:
        text += f"*NSET, NSET={load_block['set_name']}\n"
        text += "\n".join(_format_id_list(load_block["nodes"])) + "\n"
    text += f"*MATERIAL, NAME={material_name}\n"
    text += "*ELASTIC\n"
    text += f"{elastic_modulus}, {poisson_ratio}\n"
    text += f"*SOLID SECTION, ELSET=Volume, MATERIAL={material_name}\n"
    text += "*BOUNDARY\n"
    for boundary_dof in boundary_dofs:
        text += f"FIXED_SELECTION, {boundary_dof}, {boundary_dof}, 0.0\n"
    text += "*STEP\n"
    text += "*STATIC\n"
    text += "*CLOAD\n"
    for load_block in load_blocks:
        text += f"{load_block['set_name']}, {load_block['dof']}, {load_block['nodal_force']}\n"
    text += "*NODE FILE\n"
    text += "U\n"
    text += "*EL FILE\n"
    text += "S\n"
    text += "*END STEP\n"

    model_inp_path.parent.mkdir(parents=True, exist_ok=True)
    model_inp_path.write_text(text, encoding="utf-8")
