# YiYaoFlow 后端

本目录是 YiYaoFlow 的 FastAPI 后端，负责几何、网格、前处理、求解器插件、结果转换、任务状态和受控文件访问。

后端的主流程为：

```text
geometry -> mesh -> preprocess -> solver plugin -> results -> controlled file API
```

## 环境准备

后端使用 `uv` 管理 Python 环境，要求 Python `>=3.11`。

```powershell
cd backend
uv python pin 3.11
uv sync
```

Python 依赖包括 FastAPI、Gmsh、meshio、NumPy、SciPy、VTK 和 PyVista。CalculiX 等求解器可执行文件不由 `uv` 安装，需要通过插件目录或环境变量单独提供。

## 启动服务

```powershell
cd backend
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

健康检查：

```text
GET http://127.0.0.1:8000/api/health
```

FastAPI 文档页面：

```text
http://127.0.0.1:8000/docs
```

## 配置项

配置定义在 `app/core/config.py`，可通过环境变量覆盖。

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `APP_NAME` | `Minimal Cloud CAE Demo Backend` | 应用名称 |
| `API_PREFIX` | `/api` | API 前缀 |
| `CORS_ORIGINS` | `http://localhost:5173`, `http://127.0.0.1:5173` | 前端跨域白名单 |
| `CCX_EXECUTABLE` | 本机 CalculiX 示例路径 | CalculiX 回退可执行文件路径 |
| `WORKSPACE_ROOT` | `backend/app/workspace` | 算例产物目录 |

Windows PowerShell 示例：

```powershell
$env:CCX_EXECUTABLE="E:\CalculiX-2.23.0-win-x64\bin\ccx.exe"
```

## 核心 API

| API | 说明 |
| --- | --- |
| `POST /api/geometry/box` | 创建长方体几何 |
| `POST /api/geometry/sphere` | 创建球体几何 |
| `POST /api/geometry/cylinder` | 创建圆柱体几何 |
| `POST /api/geometry/step` | 导入 STEP/STP 几何 |
| `POST /api/mesh/tasks` | 启动网格生成任务 |
| `POST /api/preprocess/material` | 保存材料参数 |
| `POST /api/preprocess/boundary` | 保存固定节点和自由度 |
| `POST /api/preprocess/load` | 保存一个或多个载荷项 |
| `GET /api/solver/plugins` | 获取可用求解器插件 |
| `POST /api/solver/tasks` | 启动求解任务 |
| `GET /api/tasks/{task_id}` | 查询任务状态和日志 |
| `GET /api/results/{result_id}/summary` | 获取结果摘要 |
| `GET /api/results/{result_id}/field?field=displacement\|von_mises` | 获取位移或应力云图文件 |
| `GET /api/files/{job_id}/{stage}/{filename}` | 下载受控工作区文件 |

任务接口会返回 `task_id`，前端按 `GET /api/tasks/{task_id}` 轮询 `status`、`progress`、`phase`、`message`、`logs`、`result` 和 `error`。

## 工作区文件

后端产物位于 `WORKSPACE_ROOT` 下，默认是：

```text
backend/app/workspace/
└── job_abcdef123456/
    ├── geometry/
    ├── mesh/
    ├── preprocess/
    ├── solver/
    └── results/
```

业务 API 返回 `FileReference`，其 `path` 是逻辑路径，例如：

```text
workspace/job_abcdef123456/results/result_surface_displacement.vtp
```

浏览器不能直接读取该路径，应通过受控文件 API 访问：

```text
GET /api/files/job_abcdef123456/results/result_surface_displacement.vtp
```

文件 API 会校验 `job_id`、阶段名、文件名白名单和路径边界，避免暴露任意本地文件。

## 求解器插件

后端启动时通过 `app/services/structural_plugins/manager.py` 扫描：

```text
backend/app/plugins/*/plugin.yaml
```

插件目录最小结构：

```text
backend/app/plugins/Calculix/
├── plugin.yaml
├── adapter.py
└── bin/
    └── ccx.exe
```

`plugin.yaml` 示例：

```yaml
id: calculix
name: CalculiX
version: "2.23"
backend: python
entry: adapter.py
class: CalculiXPlugin
executable: bin/ccx.exe
```

适配器类必须继承 `StructuralSolverPlugin` 并实现：

```python
def solve(self, request: SolverRunRequest, emit=None) -> SolverRunResponse:
    ...
```

当前仓库的 `.gitignore` 忽略 `backend/app/plugins/**`，因此开源克隆后可能没有任何求解器插件。需要先自行放置插件目录；如果 CalculiX 插件已注册但未携带 `ccx.exe`，再通过 `CCX_EXECUTABLE` 指向外部可执行文件。

新增插件请参考 [../docs/如何新增求解器插件(1).md](../docs/如何新增求解器插件(1).md)。

## 求解流程约束

- 当前结构求解流程面向静力分析。
- 求解要求有效体网格；表面网格只用于预览。
- `POST /api/solver/tasks` 必须传入 `solver_plugin_id`。
- 多载荷项会写成多个节点集，并在同一个静力步中叠加。
- 结果转换会输出 `result.vtu`、`result_surface_displacement.vtp`、`result_surface_von_mises.vtp` 和 `result_summary.json`。

## 本地检查

如果项目中存在测试目录，可从仓库根目录运行：

```powershell
backend/.venv/Scripts/python.exe -m pytest -q
```

或在 `backend` 目录使用 uv：

```powershell
uv run pytest ../test
```

如果当前开源副本没有 `test/` 目录，上述命令会因为找不到测试而失败，这是预期情况。

## 常见排错

- `GET /api/solver/plugins` 返回空列表：检查 `backend/app/plugins/` 是否存在插件目录和 `plugin.yaml`。
- 插件加载时报 `Plugin entry file not found`：确认 `plugin.yaml` 的 `entry` 文件存在。
- 插件加载时报 `Plugin class ... not found`：确认 `class` 字段与 `adapter.py` 中的类名完全一致。
- 求解时报找不到 `ccx.exe`：检查插件 `executable` 路径，或设置 `CCX_EXECUTABLE`。
- STEP 能显示但不能求解：当前几何可能只生成了表面网格，检查网格响应中的 `analysis_ready`。
