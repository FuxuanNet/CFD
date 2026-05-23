from __future__ import annotations

import json
import re
from pathlib import Path

import meshio
import numpy as np
import pyvista as pv


def _array_magnitude(values: np.ndarray) -> np.ndarray:
    if values.ndim == 1:
        return np.abs(values)
    return np.linalg.norm(values, axis=1)


def _find_array(dataset: pv.DataSet, names: list[str], location: str) -> tuple[str | None, np.ndarray | None]:
    data = dataset.point_data if location == "point" else dataset.cell_data
    lower_map = {name.lower(): name for name in data.keys()}
    for wanted in names:
        found = lower_map.get(wanted.lower())
        if found:
            return found, np.asarray(data[found])
    for name in data.keys():
        lowered = name.lower()
        if any(wanted.lower() in lowered for wanted in names):
            return name, np.asarray(data[name])
    return None, None


def _split_frd_fixed_width_values(payload: str, count: int) -> list[float]:
    values: list[float] = []
    cursor = 0
    length = len(payload)
    while cursor < length and len(values) < count:
        while cursor < length and payload[cursor].isspace():
            cursor += 1
        if cursor >= length:
            break
        start = cursor
        if payload[cursor] in "+-":
            cursor += 1
        while cursor < length and payload[cursor].isdigit():
            cursor += 1
        if cursor < length and payload[cursor] == ".":
            cursor += 1
        while cursor < length and payload[cursor].isdigit():
            cursor += 1
        if cursor < length and payload[cursor] in "Ee":
            cursor += 1
            if cursor < length and payload[cursor] in "+-":
                cursor += 1
            while cursor < length and payload[cursor].isdigit():
                cursor += 1
        token = payload[start:cursor].strip()
        if token:
            values.append(float(token))
    return values


def _build_result_warnings(
    *,
    fixed_node_ids: list[int] | None = None,
    load_node_ids: list[int] | None = None,
    max_displacement: float,
) -> list[str]:
    warnings: list[str] = []
    fixed_count = len(fixed_node_ids or [])
    load_count = len(load_node_ids or [])

    if fixed_count <= 1:
        warnings.append("固定节点过少，模型可能存在刚体漂移，结果仅供参考。")
    elif fixed_count <= 3:
        warnings.append("固定节点较少，请确认约束能够充分抑制整体刚体运动。")

    if load_count <= 1:
        warnings.append("载荷仅作用在极少节点上，局部奇异和结果失真风险较高。")
    elif load_count <= 3:
        warnings.append("载荷节点较少，请确认施加载荷方式符合预期。")

    if max_displacement >= 1e8:
        warnings.append("最大位移异常大，结果可能不可信，请优先检查约束与载荷设置。")

    return warnings


def write_surface_results(
    result_vtu: Path,
    results_path: Path,
    *,
    fixed_node_ids: list[int] | None = None,
    load_node_ids: list[int] | None = None,
) -> dict[str, object]:
    """Write frontend VTP files and a JSON summary from a VTU result."""

    dataset = pv.read(result_vtu)
    surface = dataset.extract_surface(algorithm="dataset_surface")

    original_point_ids = np.asarray(surface.point_data.get("vtkOriginalPointIds", []), dtype=np.int64)
    if "node_id" in dataset.point_data and len(original_point_ids):
        surface.point_data["node_id"] = np.asarray(dataset.point_data["node_id"])[original_point_ids]
    elif "node_id" in dataset.point_data and surface.n_points == dataset.n_points:
        surface.point_data["node_id"] = np.asarray(dataset.point_data["node_id"])

    displacement_name, displacement = _find_array(dataset, ["U", "DISP", "displacement"], "point")
    stress_name, stress = _find_array(dataset, ["von_mises", "Mises"], "point")
    stress_location = "point"
    if stress is None:
        stress_name, stress = _find_array(dataset, ["Mises", "S", "stress"], "cell")
        stress_location = "cell"

    if displacement is not None:
        displacement_mag = _array_magnitude(displacement)
        max_displacement = float(displacement_mag.max()) if len(displacement_mag) else 0.0
        if displacement_name in surface.point_data:
            surface.point_data["displacement"] = _array_magnitude(np.asarray(surface.point_data[displacement_name]))
    else:
        max_displacement = 0.0
        surface.point_data["displacement"] = np.zeros(surface.n_points)

    if stress is not None:
        stress_values = _array_magnitude(stress)
        max_von_mises = float(stress_values.max()) if len(stress_values) else 0.0
        if stress_location == "point" and stress_name in surface.point_data:
            surface.point_data["von_mises"] = _array_magnitude(np.asarray(surface.point_data[stress_name]))
        elif stress_name in surface.cell_data:
            surface.cell_data["von_mises"] = _array_magnitude(np.asarray(surface.cell_data[stress_name]))
        else:
            surface.point_data["von_mises"] = np.zeros(surface.n_points)
    else:
        max_von_mises = 0.0
        surface.point_data["von_mises"] = np.zeros(surface.n_points)

    displacement_surface = results_path / "result_surface_displacement.vtp"
    stress_surface = results_path / "result_surface_von_mises.vtp"
    surface.save(displacement_surface)
    surface.save(stress_surface)
    warnings = _build_result_warnings(
        fixed_node_ids=fixed_node_ids,
        load_node_ids=load_node_ids,
        max_displacement=max_displacement,
    )

    summary = {
        "max_displacement": max_displacement,
        "max_von_mises": max_von_mises,
        "warnings": warnings,
        "arrays": {
            "displacement": displacement_name,
            "stress": stress_name,
        },
        "files": {
            "result_vtu": "result.vtu",
            "displacement": displacement_surface.name,
            "von_mises": stress_surface.name,
        },
    }
    (results_path / "result_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def _parse_fixed_width_values(line: str, count: int) -> tuple[int, list[float]]:
    payload = line[3:].rstrip("\n")
    node_id = int(payload[:10])
    values = _split_frd_fixed_width_values(payload[10:], count)
    return node_id, values


def parse_frd_displacements(frd_path: Path) -> dict[int, tuple[float, float, float]]:
    """Parse the DISP nodal result block from a CalculiX FRD file."""

    lines = frd_path.read_text(encoding="latin-1").splitlines()
    displacements: dict[int, tuple[float, float, float]] = {}
    in_disp = False
    disp_header: str | None = None
    sample_line: str | None = None
    for line in lines:
        if re.match(r"^\s*-4\s+DISP\b", line):
            in_disp = True
            disp_header = line.strip()
            continue
        if in_disp and line.strip() == "-3":
            break
        if in_disp and re.match(r"^\s*-1\b", line):
            sample_line = sample_line or line.strip()
            node_id, values = _parse_fixed_width_values(line, 3)
            if len(values) == 3:
                displacements[node_id] = (values[0], values[1], values[2])
    if not displacements:
        details = []
        if disp_header:
            details.append(f"Found header: {disp_header}")
        if sample_line:
            details.append(f"Sample line: {sample_line}")
        suffix = f" {' '.join(details)}" if details else ""
        raise ValueError(
            "No DISP block found in FRD file. Check solver.log for an unconstrained model, invalid node selections, "
            f"or missing displacement output.{suffix}"
        )
    return displacements


def parse_frd_stress(frd_path: Path) -> dict[int, tuple[float, float, float, float, float, float]]:
    """Parse the STRESS nodal result block from a CalculiX FRD file."""

    lines = frd_path.read_text(encoding="latin-1").splitlines()
    stress: dict[int, tuple[float, float, float, float, float, float]] = {}
    in_stress = False
    for line in lines:
        if re.match(r"^\s*-4\s+STRESS\b", line):
            in_stress = True
            continue
        if in_stress and line.strip() == "-3":
            break
        if in_stress and re.match(r"^\s*-1\b", line):
            node_id, values = _parse_fixed_width_values(line, 6)
            if len(values) == 6:
                stress[node_id] = (values[0], values[1], values[2], values[3], values[4], values[5])
    return stress


def von_mises_from_components(stress: np.ndarray) -> np.ndarray:
    """Compute Von Mises stress from SXX, SYY, SZZ, SXY, SYZ, SZX arrays."""

    sxx = stress[:, 0]
    syy = stress[:, 1]
    szz = stress[:, 2]
    sxy = stress[:, 3]
    syz = stress[:, 4]
    szx = stress[:, 5]
    return np.sqrt(
        0.5 * ((sxx - syy) ** 2 + (syy - szz) ** 2 + (szz - sxx) ** 2)
        + 3.0 * (sxy**2 + syz**2 + szx**2)
    )


def build_results_from_mesh_and_frd(
    mesh_inp_path: Path,
    frd_path: Path,
    results_path: Path,
    node_ids: list[int] | None = None,
    fixed_node_ids: list[int] | None = None,
    load_node_ids: list[int] | None = None,
) -> Path:
    """Build VTU/VTP result files from CalculiX output."""

    mesh = meshio.read(mesh_inp_path)
    displacements = parse_frd_displacements(frd_path)
    stress = parse_frd_stress(frd_path)
    if node_ids is None:
        node_ids = list(range(1, len(mesh.points) + 1))
    if len(node_ids) != len(mesh.points):
        raise ValueError("Mesh point count does not match node ID metadata.")
    point_u = np.zeros((len(mesh.points), 3))
    point_stress = np.zeros((len(mesh.points), 6))
    for index, node_id in enumerate(node_ids):
        if node_id in displacements:
            point_u[index] = displacements[node_id]
        if node_id in stress:
            point_stress[index] = stress[node_id]
    point_von_mises = von_mises_from_components(point_stress)

    cells = [(block.type, block.data) for block in mesh.cells if block.type == "tetra"]
    if not cells:
        cells = [(block.type, block.data) for block in mesh.cells]

    result_mesh = meshio.Mesh(
        points=mesh.points,
        cells=cells,
        point_data={
            "node_id": np.asarray(node_ids, dtype=np.int64),
            "displacement": point_u,
            "stress": point_stress,
            "von_mises": point_von_mises,
        },
    )
    results_path.mkdir(parents=True, exist_ok=True)
    result_vtu = results_path / "result.vtu"
    meshio.write(result_vtu, result_mesh)
    write_surface_results(
        result_vtu,
        results_path,
        fixed_node_ids=fixed_node_ids,
        load_node_ids=load_node_ids,
    )
    return result_vtu
