# CAE Demo Frontend

Vue 3 + VTK.js frontend for the minimal cloud CAE demo. The app provides one workbench page for the solid CAE flow:

```text
create/import STEP geometry -> generate repaired mesh -> select fixed nodes and multiple load node sets -> solve -> view contours
```

The implementation uses JavaScript with Vue `script setup`, Vue Router, Element Plus on-demand imports, and VTK.js for `.vtp` geometry/result rendering.

## Project Structure

```text
src/
  api/
    client.js        # fetch wrapper, error handling, FileReference URL conversion
    geometry.js      # geometry endpoints
    mesh.js          # mesh endpoint
    preprocess.js    # material / boundary / load endpoints
    solver.js        # solve endpoint
    results.js       # summary / field endpoints
    projects.js      # case/project persistence endpoints
  components/
    GeometryPanel.vue
    MeshPanel.vue
    MaterialPanel.vue
    BoundaryLoadPanel.vue
    ResultPanel.vue
    FileFlowPanel.vue
    StatusLog.vue
    VtkViewport.vue
  views/
    CaeWorkbenchView.vue
```

## Backend Address

By default the frontend calls `/api`. In development, `vite.config.js` proxies `/api` to:

```text
http://127.0.0.1:8000
```

You can override the API base URL with:

```powershell
$env:VITE_API_BASE_URL="http://127.0.0.1:8000/api"
```

## FileReference Conversion

Backend business APIs return logical file references:

```text
workspace/job_abcdef123456/results/result_surface_displacement.vtp
```

These are not direct static URLs. `src/api/client.js` converts them to the controlled backend file API:

```text
/api/files/job_abcdef123456/results/result_surface_displacement.vtp
```

VTK.js loads geometry previews, mesh previews, and contour surfaces through that controlled endpoint. Mesh previews include a `node_id` point-data array used by browser picking.

## Run

Start the backend first:

```powershell
cd ../backend
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Then start the frontend:

```powershell
cd ../front
npm install
npm run dev
```

Open the URL printed by Vite, usually:

```text
http://127.0.0.1:5173/
```

## Build

```powershell
npm run build
```

VTK.js is large, so Vite may warn about a chunk larger than 500 kB. That warning is expected for the current single-page demo.

## Manual Flow Check

1. Click `创建梁` or import a STEP file. STEP preview renders the actual surface, not a bounding box.
2. Click `生成网格`. Closed solid models return `analysis_ready=true`; surface-only models remain display-only.
3. Click `生成网格`. The frontend starts a backend mesh task and polls `/api/tasks/{task_id}` so long STEP files show phase, progress, elapsed state, and mesh logs while running.
4. In `约束 / 载荷`, click `选点` for fixed nodes, then click or drag-box in the VTK viewport. While node selection is active, viewport rotation/pan is locked so selection and camera control do not conflict.
5. Add one or more load items. Each item has its own direction, total force, and node set; a load item can reuse the previous item's nodes and then append or remove nodes by selection.
6. Click `保存前处理` or `开始求解`. Solver runs through the same task polling flow and writes logs to the solver tab.
7. Switch between `位移` and `Von Mises` in the result panel.
8. Open files from `文件链路` to verify controlled artifact downloads.

When node selection is active, single clicks toggle one mesh node and drag boxes append or remove all visible nodes inside the rectangle based on the selection operation. Fixed nodes, all load nodes, and the active load item are highlighted with separate colors and preserved when switching selection modes.

If STEP preview generation fails, the empty VTK viewport shows the backend error detail instead of silently staying at the waiting state.

The bottom log dock has separate tabs for message, mesh, solver, and error logs. Task logs are de-duplicated by task ID and sequence number while polling.
