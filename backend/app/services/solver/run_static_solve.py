import subprocess
from collections.abc import Callable
from pathlib import Path

from app.core.config import get_settings
from app.core.workspace import read_json, require_file, workspace_api_path
from app.schemas.common import FileReference
from app.schemas.solver import SolverRunRequest, SolverRunResponse
from app.services.cae_files import mesh_dir, preprocess_dir, results_dir, solver_dir
from app.services.results.result_converter import build_results_from_mesh_and_frd
from app.services.solver.inp_writer import write_model_inp
from app.services.structural_plugins.manager import get_structural_solver_manager


ProgressCallback = Callable[[str, int, str, str], None]


def _noop_progress(_phase: str, _progress: int, _message: str, _channel: str = "solver") -> None:
    return None


def _clean_previous_outputs(paths: list[Path]) -> None:
    for path in paths:
        path.unlink(missing_ok=True)


def run_static_solve(request: SolverRunRequest, progress: ProgressCallback | None = None) -> SolverRunResponse:
    """Run a static linear solve for the prepared beam model.

    Input:
        mesh_id, material_id, boundary_id, and load_id.

    Return:
        Result ID plus placeholder INP, FRD, DAT, and solver log paths.

    This implementation writes model.inp, runs CalculiX, converts FRD, and writes result files.
    """

    result_id = request.mesh_id
    emit = progress or _noop_progress
    mesh_path = mesh_dir(request.mesh_id)
    preprocess_path = preprocess_dir(request.mesh_id)
    out_dir = solver_dir(result_id)
    result_path = results_dir(result_id)

    mesh_inp_path = require_file(mesh_path / "mesh.inp", "Mesh INP file not found.")
    mesh_sets_path = require_file(mesh_path / "mesh_sets.json", "Mesh node sets file not found.")
    material_path = require_file(preprocess_path / "material.json", "Material config not found.")
    boundary_path = require_file(preprocess_path / "boundary.json", "Boundary config not found.")
    load_path = require_file(preprocess_path / "load.json", "Load config not found.")
    emit("solver_prepare", 10, "Solver inputs found.", "solver")

    model_inp_path = out_dir / "model.inp"
    model_frd_path = out_dir / "model.frd"
    model_dat_path = out_dir / "model.dat"
    solver_log_path = out_dir / "solver.log"
    _clean_previous_outputs(
        [
            model_frd_path,
            model_dat_path,
            out_dir / "model.cvg",
            out_dir / "model.sta",
            out_dir / "model.12d",
            result_path / "result.vtu",
            result_path / "result_surface_displacement.vtp",
            result_path / "result_surface_von_mises.vtp",
            result_path / "result_summary.json",
        ]
    )
    emit("solver_prepare", 18, "Previous solver and result outputs cleaned.", "solver")

    mesh_sets = read_json(mesh_sets_path)
    boundary = read_json(boundary_path)
    load = read_json(load_path)
    emit("solver_inp", 25, "Writing CalculiX model input.", "solver")
    write_model_inp(
        mesh_inp_path=mesh_inp_path,
        model_inp_path=model_inp_path,
        mesh_sets=mesh_sets,
        material=read_json(material_path),
        boundary=boundary,
        load=load,
    )
    emit("solver_run", 38, "CalculiX process starting.", "solver")

    plugin = get_structural_solver_manager().get_plugin(request.solver_plugin_id)
    ccx_path = plugin.executable_path
    ccx = str(ccx_path if ccx_path.exists() else get_settings().CCX_EXECUTABLE)
    command = [ccx, "-i", "model"]
    try:
        completed = subprocess.run(
            command,
            cwd=out_dir,
            text=True,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError as exc:
        solver_log_path.write_text(f"CalculiX executable not found: {ccx}\n", encoding="utf-8")
        emit("solver_error", 40, f"CalculiX executable not found: {ccx}", "error")
        raise RuntimeError(f"CalculiX executable not found: {ccx}") from exc

    emit("solver_run", 72, f"CalculiX process finished with exit code {completed.returncode}.", "solver")
    solver_log_path.write_text(
        "command: " + " ".join(command) + "\n\n"
        "--- stdout ---\n"
        + completed.stdout
        + "\n--- stderr ---\n"
        + completed.stderr,
        encoding="utf-8",
    )
    if completed.returncode != 0:
        emit("solver_error", 72, f"CalculiX failed with exit code {completed.returncode}.", "error")
        raise RuntimeError(f"CalculiX failed with exit code {completed.returncode}")
    require_file(model_frd_path, "CalculiX did not produce model.frd.")

    emit("solver_results", 82, "Converting FRD results to VTK files.", "solver")
    build_results_from_mesh_and_frd(
        mesh_inp_path,
        model_frd_path,
        result_path,
        node_ids=[int(node_id) for node_id in mesh_sets.get("node_ids", [])],
        fixed_node_ids=[int(node_id) for node_id in boundary.get("node_ids", [])],
        load_node_ids=[int(node_id) for load_item in load.get("loads", []) for node_id in load_item.get("node_ids", [])],
    )
    summary = read_json(result_path / "result_summary.json")
    for warning in summary.get("warnings", []):
        emit("solver_warning", 92, str(warning), "solver")
    emit("solver_done", 100, "Static solve completed and result files are ready.", "solver")

    files = [
        FileReference(name="model.inp", path=workspace_api_path(model_inp_path), description="CalculiX input file."),
        FileReference(name="model.frd", path=workspace_api_path(model_frd_path), description="CalculiX result file."),
        FileReference(name="solver.log", path=workspace_api_path(solver_log_path), description="Solver stdout/stderr log."),
        FileReference(name="result.vtu", path=workspace_api_path(result_path / "result.vtu"), description="Converted unstructured grid result."),
        FileReference(name="result_surface_displacement.vtp", path=workspace_api_path(result_path / "result_surface_displacement.vtp"), description="Displacement cloud plot surface."),
        FileReference(name="result_surface_von_mises.vtp", path=workspace_api_path(result_path / "result_surface_von_mises.vtp"), description="Von Mises cloud plot surface."),
        FileReference(name="result_summary.json", path=workspace_api_path(result_path / "result_summary.json"), description="Result maximum values."),
    ]
    if model_dat_path.exists():
        files.insert(2, FileReference(name="model.dat", path=workspace_api_path(model_dat_path), description="CalculiX text output."))

    return SolverRunResponse(
        message="Static solve completed.",
        result_id=result_id,
        status="completed",
        files=files,
    )
