# YiYaoFlow 前端

本目录是 YiYaoFlow 的 Vue 3 前端工作台，提供几何、网格、材料、边界载荷、求解和结果查看的一页式 CAE 操作界面。

前端使用 VTK.js 渲染几何、网格和结果云图，使用 Pinia 保存工作流状态，使用 Element Plus 构建表单和交互控件。

## 环境要求

- Node.js `^20.19.0 || >=22.12.0`
- npm
- 已启动的后端服务：`http://127.0.0.1:8000`

## 安装与启动

```powershell
cd front
npm install
npm run dev
```

访问 Vite 输出的地址，通常是：

```text
http://127.0.0.1:5173/
```

## 后端地址

默认情况下，前端请求 `/api`。开发服务器通过 `vite.config.js` 代理到：

```text
http://127.0.0.1:8000
```

如果前端需要直接访问其他后端地址，可以设置：

```powershell
$env:VITE_API_BASE_URL="http://127.0.0.1:8000/api"
npm run dev
```

## 主要功能

- 算例管理：创建、打开、重命名、删除算例。
- 几何：创建长方体、球体、圆柱体，或导入 STEP/STP 文件。
- 网格：提交异步网格任务，并显示任务进度、阶段和日志。
- 前处理：设置材料，选择固定节点，维护一个或多个载荷节点集。
- 求解：从后端读取求解器插件列表，提交异步求解任务。
- 结果：查看位移和 Von Mises 应力云图。
- 文件链路：通过受控文件 API 打开几何、网格、求解和结果产物。

## 项目结构

```text
src/
├── api/                    # 后端 API 封装和 FileReference 转换
├── components/             # 工作台面板、VTK 视口和日志组件
├── components/workbench/   # 工作台布局组件
├── router/                 # Vue Router
├── stores/                 # Pinia 工作流状态
├── views/                  # CaeWorkbenchView 主页面
├── App.vue
└── main.js
```

## FileReference 转换

后端业务 API 返回的文件路径是逻辑路径：

```text
workspace/job_abcdef123456/results/result_surface_displacement.vtp
```

它不是浏览器静态 URL。`src/api/client.js` 会把它转换为：

```text
/api/files/job_abcdef123456/results/result_surface_displacement.vtp
```

VTK.js 通过该受控接口加载几何预览、网格预览和结果云图。

## 工作流检查

启动前后端后，可以按下面流程手动验收：

1. 打开页面，确认左侧出现默认算例或可创建新算例。
2. 在“几何”步骤创建参数化几何，或导入 STEP/STP 文件，确认 3D 视口出现预览。
3. 进入“网格”步骤生成网格，确认底部日志出现任务进度，视口显示网格。
4. 设置材料参数。
5. 在“载荷”步骤选择固定节点，再添加载荷项并选择载荷节点。
6. 在“求解”步骤选择求解器插件并开始求解。
7. 求解完成后进入“结果”步骤，切换位移和 Von Mises 应力云图。
8. 打开“文件”步骤，确认产物文件可以通过后端受控接口访问。

如果 STEP 只能生成表面网格，页面会显示预览，但后续求解步骤会被阻止。

## 构建

```powershell
npm run build
```

本项目使用 VTK.js，构建时可能出现大 chunk 警告。当前单页工作台场景下这是预期现象。

## 常见排错

- 页面提示后端连接失败：确认后端已在 `127.0.0.1:8000` 启动，或检查 `VITE_API_BASE_URL`。
- 求解器下拉为空：确认后端 `GET /api/solver/plugins` 能返回插件列表。
- VTK 视口空白：先检查后端文件 API 是否能访问对应 `.vtp` 文件。
- 载荷/求解步骤无法进入：确认已经生成可求解体网格，并完成固定节点和载荷节点选择。
