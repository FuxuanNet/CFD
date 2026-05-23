# CAE Demo Backend

FastAPI backend for the minimal cloud CAE demo. It runs the current solid-analysis flow:

```text
geometry -> repaired mesh -> material/node selections/load -> CalculiX solve -> VTK result files
```

The current backend also includes a minimal structural solver plugin system. The UI no longer hardcodes a single solver name; it asks the backend for available structural solvers and sends the chosen `solver_plugin_id` when starting a solve.

The API keeps generated artifacts in `app/workspace/{job_id}/`, but clients must not read that directory directly. File access goes through the controlled files API described below.

## Environment With uv

```powershell
cd backend
uv python pin 3.11
uv sync
```

The project uses `gmsh`, `meshio`, `numpy`, `vtk`, and `pyvista`. CalculiX is an external command line solver and is not installed by uv.

## CalculiX

If `ccx` is available in `PATH`, no extra setting is needed. Otherwise point the backend to the executable:

```powershell
$env:CCX_EXECUTABLE="E:\CalculiX-2.23.0-win-x64\bin\ccx.exe"
```

Optional direct check:

```powershell
& "E:\CalculiX-2.23.0-win-x64\bin\ccx.exe"
```

## Structural Solver Plugin System

The backend uses a minimal structural solver plugin system so the frontend does not hardcode one solver. Each plugin lives under `app/plugins/<PluginName>/` and contains a `plugin.yaml` plus a Python adapter class. Current example:

```text
app/plugins/
  CalculiX/
    plugin.yaml
    adapter.py
    bin/
      ccx.exe
```

Example manifest:

```yaml
id: calculix
name: CalculiX
version: "2.23"
backend: python
entry: adapter.py
class: CalculiXPlugin
executable: bin/ccx.exe
```

How it works:

1. `app/services/structural_plugins/manager.py` scans `app/plugins/*/plugin.yaml`, validates the manifest, loads the adapter module from `entry`, and resolves the adapter class from `class`.
2. `GET /api/solver/plugins` returns the discovered plugin list to the frontend.
3. The frontend sends the chosen `solver_plugin_id` in `POST /api/solver/run` or `POST /api/solver/tasks`.
4. `app/api/solver_api.py` creates the plugin instance with `get_structural_solver_manager().create_plugin(request.solver_plugin_id)` and calls `solve(...)`.
5. The current `CalculiXPlugin` is a thin adapter that delegates to the existing `run_static_solve(...)` pipeline.

Current request flow:

```text
Frontend
  -> GET /api/solver/plugins
  -> user selects solver plugin id
  -> POST /api/solver/tasks with solver_plugin_id
  -> backend creates plugin instance
  -> plugin.solve(request, emit)
  -> existing static solve pipeline runs
  -> result files returned as before
```

Executable resolution is also plugin-based: `run_static_solve` first uses the executable path declared in `plugin.yaml`, and falls back to `CCX_EXECUTABLE` if that file does not exist.

To add a new structural solver, create a new directory under `app/plugins/`, add `plugin.yaml`, and implement an adapter class derived from `StructuralSolverPlugin`. This first version is intentionally minimal: each solver family still needs its own adapter, and the request shape is still focused on static structural analysis.

Key call site:

```python
get_structural_solver_manager().create_plugin(request.solver_plugin_id).solve(...)
```

## Run API Server

```powershell
cd backend
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Health check:

```text
GET http://127.0.0.1:8000/api/health
```

## API Flow

All successful responses keep the current root-level shape, for example `success`, `message`, `geometry_id`, `mesh_id`, `files`, and so on. They are not wrapped in a `data` object.

```text
POST /api/geometry/box
POST /api/geometry/step
POST /api/mesh/generate
POST /api/mesh/tasks
POST /api/preprocess/material
POST /api/preprocess/boundary
POST /api/preprocess/load
GET  /api/solver/plugins
POST /api/solver/run
POST /api/solver/tasks
GET  /api/tasks/{task_id}
GET  /api/results/{result_id}/summary
GET  /api/results/{result_id}/field?field=displacement|von_mises
```

STEP import writes a real surface `geometry_preview.vtp` for browser rendering. Mesh generation tries raw STEP solid meshing first, then healed solid meshing, then surface-mesh fallback. This avoids damaging valid periodic solids such as `sphere_d10.0.step` during healing. If the STEP cannot form a closed volume, the backend still returns a displayable surface mesh with `mesh_kind="surface"` and `analysis_ready=false`.

The current solver supports solid elements only. Surface-only or broken STEP models can be displayed and inspected, but they are not sent to CalculiX until they form a valid volume mesh.

Long-running mesh and solver operations can also be run through task endpoints. `POST /api/mesh/tasks` and `POST /api/solver/tasks` return a `task_id`; poll `GET /api/tasks/{task_id}` for `status`, `progress`, `phase`, `message`, typed `logs`, `result`, and `error`. Log channels are `message`, `mesh`, `solver`, and `error`.

Solver execution now requires `solver_plugin_id`, because the solver is chosen through the plugin manager instead of being hardcoded.

Boundary setup uses explicit fixed mesh node selections:

```json
{
  "mesh_id": "job_abcdef123456",
  "node_ids": [1, 2, 3],
  "dofs": [1, 2, 3]
}
```

Load setup accepts either the legacy single-load shape or multiple force items in one static step:

```json
{
  "mesh_id": "job_abcdef123456",
  "loads": [
    { "id": "load_1", "name": "F1", "node_ids": [8, 9], "direction": "x", "magnitude": 120 },
    { "id": "load_2", "name": "F2", "node_ids": [10, 11], "direction": "z", "magnitude": -240 }
  ]
}
```

Each force item is written as its own `LOAD_SELECTION_n` node set and `*CLOAD` entry. Overlapping node sets are allowed; CalculiX naturally superposes the loads in the same static step.

`mesh_preview.vtp` includes a `node_id` point-data array so the frontend can map VTK.js point picks back to CalculiX node IDs.

`FileReference.path` values are logical workspace references such as:

```text
workspace/job_abcdef123456/results/result_surface_displacement.vtp
```

They are not browser URLs.

## Controlled File API

Generated files are exposed through:

```text
GET /api/files/{job_id}/{stage}/{filename}
```

Example:

```text
GET /api/files/job_abcdef123456/results/result_surface_displacement.vtp
```

Security rules:

- `job_id` must match `job_[0-9a-f]{12}`.
- `stage` must be one of `geometry`, `mesh`, `preprocess`, `solver`, or `results`.
- `filename` must be a plain filename and must be included in that stage's allowlist.
- The resolved path must remain inside `WORKSPACE_ROOT`.
- Directory listing, absolute paths, `..`, and unlisted files are rejected.

This keeps the existing workspace file contract while avoiding a raw static mount of the whole workspace directory.

## Run Tests

From the repository root:

```powershell
backend/.venv/Scripts/python.exe -m pytest -q
```

Or from `backend` with uv:

```powershell
uv run pytest ../test
```

## Current Scope

- Parameterized box geometry and STEP import.
- Raw-first Gmsh volume mesh generation, geometry healing fallback, and surface-mesh fallback for display.
- Task polling with typed logs for long mesh and solver operations.
- Material, fixed node selection, and multiple load node selection persistence.
- CalculiX input writing and solve execution.
- FRD parsing/conversion to VTU/VTP result files.
- Result summary and field APIs for displacement and Von Mises plots.
- Controlled artifact download for frontend VTK.js rendering.
