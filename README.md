# YiYaoFlow：面向结构静力分析的云 CAE 工作台

YiYaoFlow 是一个前后端分离的浏览器端 CAE 工作台，覆盖结构静力分析的基础流程：几何创建或 STEP 导入、网格生成、材料与边界载荷设置、求解器计算、结果云图查看。

项目当前以 FastAPI + Vue 3 + VTK.js 为主体，后端通过插件机制接入结构求解器。默认流程适配 CalculiX，也可以通过 `plugin.yaml` 和 Python 适配器接入其他命令行或自研求解器。

## 功能特性

- 几何建模：支持长方体、球体、圆柱体参数化创建和 STEP/STP 文件导入。
- 网格生成：使用 Gmsh 生成体网格，失败时可降级生成表面网格用于显示。
- 前处理：支持材料参数、固定节点集、多载荷项和载荷方向设置。
- 求解执行：通过求解器插件动态发现和运行求解器，支持异步任务进度轮询。
- 后处理：将结果转换为 VTK 文件，在浏览器中查看位移和 Von Mises 应力云图。
- 算例管理：支持算例创建、重命名、删除和工作流状态保存。
- 文件访问：工作区产物通过受控文件 API 暴露，不直接挂载整个工作目录。

## 技术栈

| 模块      | 技术                                     |
| --------- | ---------------------------------------- |
| 前端      | Vue 3, Vite, Pinia, Element Plus, VTK.js |
| 后端      | FastAPI, Pydantic, uvicorn               |
| 几何/网格 | Gmsh, meshio                             |
| 数值/结果 | NumPy, SciPy, VTK, PyVista               |
| 求解器    | CalculiX 或其他结构求解器插件            |
| 任务调度  | ThreadPoolExecutor + API 轮询            |

## 目录结构

```text
.
├── backend/                 # FastAPI 后端、CAE 服务、求解器插件管理
├── front/                   # Vue 3 前端工作台
├── docs/                    # 设计文档、插件说明和课程材料
├── README.md                # 项目总览和快速上手
└── .gitignore
```

运行过程中后端会在 `backend/app/workspace/` 下生成算例产物。求解器插件通常放在 `backend/app/plugins/` 下；该目录被 `.gitignore` 忽略，开源分发时需要使用者自行安装插件和二进制文件。

## 环境要求

- Python `>=3.11`
- Node.js `^20.19.0 || >=22.12.0`
- uv
- npm
- CalculiX 或其他符合插件接口的结构求解器可执行文件

如果没有内置插件二进制文件，需要手动准备求解器。例如 CalculiX 插件可以通过插件目录提供 `bin/ccx.exe`；如果插件已注册但没有携带可执行文件，也可以通过环境变量指定回退路径：

```powershell
$env:CCX_EXECUTABLE="E:\CalculiX-2.23.0-win-x64\bin\ccx.exe"
```

## 快速开始

### 1. 启动后端

```powershell
cd backend
uv python pin 3.11
uv sync
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

健康检查：

```text
http://127.0.0.1:8000/api/health
```

### 2. 启动前端

另开一个终端：

```powershell
cd front
npm install
npm run dev
```

访问 Vite 输出的地址，通常是：

```text
http://127.0.0.1:5173/
```

开发环境下前端默认请求 `/api`，`front/vite.config.js` 会把它代理到 `http://127.0.0.1:8000`。

## 基本使用流程

1. 创建或导入几何：在工作台中创建参数化几何，或导入 STEP/STP 文件。
2. 生成网格：设置网格尺寸后提交网格任务，等待任务完成。
3. 设置材料：填写弹性模量和泊松比。
4. 选择节点：在 3D 视口中选择固定节点和一个或多个载荷节点集。
5. 选择求解器：前端会从 `GET /api/solver/plugins` 获取可用插件。
6. 提交求解：求解任务通过后台任务执行，前端轮询状态和日志。
7. 查看结果：切换位移或 Von Mises 应力云图，检查结果文件链路。

只有形成有效体网格的算例可以进入求解；表面网格可用于预览，但不会提交给结构求解器。

## 核心 API

| API                                            | 说明                     |
| ---------------------------------------------- | ------------------------ |
| `GET /api/health`                            | 后端健康检查             |
| `GET /api/solver/plugins`                    | 获取可用求解器插件       |
| `POST /api/mesh/tasks`                       | 启动异步网格任务         |
| `POST /api/solver/tasks`                     | 启动异步求解任务         |
| `GET /api/tasks/{task_id}`                   | 查询任务状态、进度和日志 |
| `GET /api/files/{job_id}/{stage}/{filename}` | 访问受控工作区文件       |

完整接口细节见 [backend/README.md](backend/README.md)。

## 求解器插件

每个求解器插件位于 `backend/app/plugins/<PluginName>/`，至少包含：

```text
backend/app/plugins/<PluginName>/
├── plugin.yaml
├── adapter.py
└── bin/
    └── solver executable
```

最小清单示例：

```yaml
id: calculix
name: CalculiX
version: "2.23"
backend: python
entry: adapter.py
class: CalculiXPlugin
executable: bin/ccx.exe
```

插件目录被 `.gitignore` 忽略，避免把大型求解器二进制和许可文件直接提交到仓库。克隆开源仓库后，如果 `GET /api/solver/plugins` 返回空列表，请先放置插件目录；如果插件存在但找不到求解器程序，再配置对应的外部可执行文件路径。
