<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { storeToRefs } from 'pinia'
import StatusLog from '@/components/StatusLog.vue'
import ProjectSidebar from '@/components/workbench/ProjectSidebar.vue'
import WorkbenchRightPanel from '@/components/workbench/WorkbenchRightPanel.vue'
import WorkbenchTabbar from '@/components/workbench/WorkbenchTabbar.vue'
import WorkbenchTopbar from '@/components/workbench/WorkbenchTopbar.vue'
import WorkbenchViewportPane from '@/components/workbench/WorkbenchViewportPane.vue'
import { fileUrlFromReference, findFile, getTaskStatus, normalizeError } from '@/api/client'
import { createBoxGeometry, createCylinderGeometry, createSphereGeometry, importStepGeometry } from '@/api/geometry'
import { startMeshTask } from '@/api/mesh'
import { createProject, deleteProject, getProjectSnapshot, listProjects, updateProject } from '@/api/projects'
import { setBoundary, setLoad, setMaterial } from '@/api/preprocess'
import { getResultField, getResultSummary } from '@/api/results'
import { listSolverPlugins, startSolverTask } from '@/api/solver'
import { useWorkbenchStore } from '@/stores/workbench'

const store = useWorkbenchStore()
const {
  projects,
  currentProject,
  solverPlugins,
  selectedSolverPluginId,
  activeTab,
  activeTask,
  seenTaskLogs,
  busy,
  solving,
  showEdges,
  showPoints,
  currentField,
  viewMode,
  viewportUrl,
  viewportError,
  selectedStepFile,
  activeGeometryKind,
  fixedNodeIds,
  loads,
  activeLoadId,
  selectionTarget,
  selectionActive,
  selectionOperation,
  logs,
  geometryForms,
  meshForm,
  materialForm,
  state,
  currentCaseId,
  activeLoad,
  analysisReady,
  analysisMessage,
  statusText,
} = storeToRefs(store)

const viewportRef = ref(null)
let saveTimer = 0
let loadingProject = false

const tabs = [
  { key: 'file', label: '文件' },
  { key: 'geometry', label: '几何' },
  { key: 'mesh', label: '网格' },
  { key: 'material', label: '材料' },
  { key: 'load', label: '载荷' },
  { key: 'solve', label: '求解' },
  { key: 'result', label: '结果' },
]
const workflowTabs = ['geometry', 'mesh', 'material', 'load', 'solve', 'result']
const lastActiveTab = ref(activeTab.value)
let guardingTabChange = false

const currentCaseName = computed(() => currentProject.value?.name || '未选择算例')
const activeGeometryForm = computed(() => geometryForms.value[activeGeometryKind.value] || geometryForms.value.box)
const editableGeometryKind = computed(() => (geometryForms.value[activeGeometryKind.value] ? activeGeometryKind.value : 'box'))
const hasCompleteLoadSelection = computed(() => Boolean(fixedNodeIds.value.length && loads.value.length && loads.value.every((load) => load.nodeIds?.length)))
const workflowAccess = computed(() => ({
  file: { enabled: true, message: '' },
  geometry: { enabled: true, message: '' },
  mesh: {
    enabled: Boolean(state.value.geometry?.geometry_id),
    message: '请先创建或导入几何',
  },
  material: {
    enabled: Boolean(state.value.mesh?.mesh_id && analysisReady.value),
    message: state.value.mesh?.analysis_message || '请先生成可求解网格',
  },
  load: {
    enabled: Boolean(state.value.mesh?.mesh_id && analysisReady.value),
    message: state.value.mesh?.analysis_message || '请先生成可求解网格',
  },
  solve: {
    enabled: Boolean(state.value.mesh?.mesh_id && analysisReady.value && hasCompleteLoadSelection.value),
    message: !state.value.mesh?.mesh_id
      ? '请先生成网格'
      : !analysisReady.value
        ? (analysisMessage.value || '当前网格不可求解')
        : '请先完成固定节点和所有载荷节点选择',
  },
  result: {
    enabled: Boolean(state.value.summary),
    message: '请先完成求解',
  },
}))
const nextWorkflowTab = computed(() => {
  const index = workflowTabs.indexOf(activeTab.value)
  return index >= 0 ? workflowTabs[index + 1] || '' : ''
})
const canGoNext = computed(() => Boolean(nextWorkflowTab.value && workflowAccess.value[nextWorkflowTab.value]?.enabled))
const nextTabLabel = computed(() => tabs.find((tab) => tab.key === nextWorkflowTab.value)?.label || '')
const nextBlockedMessage = computed(() => workflowAccess.value[nextWorkflowTab.value]?.message || '')
const viewportTitle = computed(() => {
  if (viewMode.value === 'result') return currentField.value === 'von_mises' ? '3D 视口 / Von Mises 应力云图' : '3D 视口 / 位移云图'
  if (viewMode.value === 'mesh') return '3D 视口 / 网格预览'
  return '3D 视口 / 几何预览'
})
const viewportSubtitle = computed(() => {
  if (viewMode.value === 'mesh') {
    const load = activeLoad.value
    const loadText = load ? `${load.name || 'F'} ${load.direction.toUpperCase()} 向 ${load.magnitude} N / ${load.nodeIds.length} nodes` : '尚未添加载荷'
    return `固定 ${fixedNodeIds.value.length} 个节点，${loads.value.length} 个力项，当前 ${loadText}。`
  }
  if (state.value.geometry?.geometry_id) return `算例 ${state.value.geometry.geometry_id}，生成网格后可在浏览器中选择节点集。`
  return '创建或导入 STEP 后显示真实几何预览。'
})

function sleep(ms) {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms)
  })
}

async function promptText(message, defaultValue = '') {
  try {
    const { value } = await ElMessageBox.prompt(message, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputValue: defaultValue,
      inputValidator: (input) => {
        if (!input?.trim()) return '请输入算例名称'
        return true
      },
    })
    return value.trim()
  } catch (error) {
    if (error === 'cancel' || error === 'close') return null
    throw error
  }
}

async function confirmAction(message) {
  try {
    await ElMessageBox.confirm(message, '确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    return true
  } catch (error) {
    if (error === 'cancel' || error === 'close') return false
    throw error
  }
}

function mergeNodeIds(current, next) {
  return Array.from(new Set([...current, ...next.map((nodeId) => Number(nodeId))])).sort((a, b) => a - b)
}

function removeNodeIds(current, next) {
  const removing = new Set(next.map((nodeId) => Number(nodeId)))
  return current.filter((nodeId) => !removing.has(Number(nodeId)))
}

function toggleNodeId(current, nodeId) {
  const normalized = Number(nodeId)
  return current.includes(normalized)
    ? current.filter((value) => value !== normalized)
    : mergeNodeIds(current, [normalized])
}

function createLoadItem(index = 1) {
  return {
    id: `load_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`,
    name: `F${index}`,
    direction: 'z',
    magnitude: -1000,
    nodeIds: [],
  }
}

function setViewportFromFile(file, mode, scalar = '') {
  const url = fileUrlFromReference(file)
  if (!url) throw new Error(`无法转换文件路径: ${file?.path || 'empty'}`)
  viewportError.value = ''
  viewportUrl.value = url
  viewMode.value = mode
  currentField.value = scalar || currentField.value
}

function resetViewportToMesh() {
  const meshPreview = findFile(state.value.mesh?.files || state.value.files || [], 'mesh_preview.vtp')
  state.value.summary = null
  state.value.field = null
  viewportError.value = ''
  selectionActive.value = false
  selectionTarget.value = 'none'
  if (meshPreview) {
    setViewportFromFile(meshPreview, 'mesh')
    return
  }
  viewportUrl.value = ''
  viewMode.value = 'mesh'
}

function scheduleProjectSave() {
  if (loadingProject || !currentProject.value?.project_id) return
  window.clearTimeout(saveTimer)
  saveTimer = window.setTimeout(() => {
    persistCurrentProject().catch((error) => {
      store.appendLog(`算例状态保存失败：${normalizeError(error)}`, 'error', 'case_save')
    })
  }, 650)
}

async function persistCurrentProject() {
  if (!currentProject.value?.project_id) return
  const response = await updateProject(currentProject.value.project_id, {
    case_id: state.value.geometry?.geometry_id || state.value.mesh?.mesh_id || state.value.solver?.result_id || currentProject.value.case_id || '',
    snapshot: store.toSnapshot(),
  })
  currentProject.value = response
  const index = projects.value.findIndex((project) => project.project_id === response.project_id)
  if (index >= 0) projects.value[index] = response
}

async function loadProjects() {
  const response = await listProjects()
  projects.value = response.projects || []
  if (projects.value.length) {
    await openProject(projects.value[0].project_id)
    return
  }
  const created = await createProject({ name: '默认算例' })
  projects.value = [created]
  await openProject(created.project_id)
}

async function refreshProjects(preferredProjectId = '') {
  const response = await listProjects()
  projects.value = response.projects || []
  const nextProjectId = preferredProjectId && projects.value.some((project) => project.project_id === preferredProjectId)
    ? preferredProjectId
    : projects.value[0]?.project_id || ''
  if (nextProjectId) {
    await openProject(nextProjectId)
    return
  }
  currentProject.value = null
  store.resetWorkspace()
}

async function loadSolverPlugins() {
  const response = await listSolverPlugins()
  solverPlugins.value = response.plugins || []
  if (!selectedSolverPluginId.value && solverPlugins.value.length) {
    selectedSolverPluginId.value = solverPlugins.value[0].id
  }
}

async function openProject(projectId) {
  loadingProject = true
  try {
    const response = await getProjectSnapshot(projectId)
    currentProject.value = response.project
    store.restoreSnapshot(response.snapshot)
    currentProject.value = response.project
    store.appendLog(`已打开算例：${response.project.name}`)
  } catch (error) {
    ElMessage.error(normalizeError(error))
  } finally {
    loadingProject = false
  }
}

async function handleCreateProject() {
  try {
    const value = await promptText('请输入算例名称', `算例 ${projects.value.length + 1}`)
    if (!value) return
    const project = await createProject({ name: value })
    projects.value = [project, ...projects.value.filter((item) => item.project_id !== project.project_id)]
    await openProject(project.project_id)
    refreshProjects(project.project_id).catch(() => null)
  } catch (error) {
    ElMessage.error(normalizeError(error))
  }
}

async function handleRenameProject(project) {
  try {
    const value = await promptText('请输入新的算例名称', project.name)
    if (!value) return
    const updated = await updateProject(project.project_id, { name: value })
    projects.value = projects.value.map((item) => (item.project_id === updated.project_id ? updated : item))
    if (currentProject.value?.project_id === updated.project_id) currentProject.value = updated
    refreshProjects(updated.project_id).catch(() => null)
  } catch (error) {
    ElMessage.error(normalizeError(error))
  }
}

async function handleDeleteProject(project) {
  try {
    if (!await confirmAction(`删除算例「${project.name}」及其产物文件？`)) return
    const fallbackProjectId = currentProject.value?.project_id === project.project_id
      ? (projects.value.find((item) => item.project_id !== project.project_id)?.project_id || '')
      : (currentProject.value?.project_id || '')
    await deleteProject(project.project_id)
    projects.value = projects.value.filter((item) => item.project_id !== project.project_id)
    if (fallbackProjectId) {
      await openProject(fallbackProjectId)
      refreshProjects(fallbackProjectId).catch(() => null)
      return
    }
    if (!projects.value.length) {
      const created = await createProject({ name: '默认算例' })
      projects.value = [created]
      await openProject(created.project_id)
      refreshProjects(created.project_id).catch(() => null)
      return
    }
    currentProject.value = null
    store.resetWorkspace()
  } catch (error) {
    ElMessage.error(normalizeError(error))
  }
}

function handleProjectMenuCommand(command, project) {
  if (command === 'rename') {
    handleRenameProject(project)
    return
  }
  if (command === 'delete') handleDeleteProject(project)
}

async function handleNewCase() {
  await handleCreateProject()
}

function goToTab(tabKey, notify = true) {
  const access = workflowAccess.value[tabKey]
  if (!access?.enabled) {
    if (notify) ElMessage.warning(access?.message || '请先完成前置流程')
    return false
  }
  activeTab.value = tabKey
  return true
}

function beforeTabLeave(nextName) {
  const access = workflowAccess.value[nextName]
  if (!access?.enabled) {
    ElMessage.warning(access?.message || '请先完成前置流程')
    return false
  }
  return true
}

function goNext() {
  if (!nextWorkflowTab.value) return
  goToTab(nextWorkflowTab.value)
}

async function waitForTask(startResponse) {
  activeTask.value = startResponse
  seenTaskLogs.value = new Set()
  while (true) {
    const task = await getTaskStatus(startResponse.task_id)
    activeTask.value = task
    store.appendTaskLogs(task)
    if (task.status === 'completed') {
      activeTask.value = task
      return task.result
    }
    if (task.status === 'failed') {
      const error = new Error(task.error || task.message || '任务失败')
      error.task = task
      throw error
    }
    await sleep(1000)
  }
}

async function runTask(tab, label, fn) {
  busy.value = true
  activeTab.value = tab
  store.appendLog(`${label}开始。`)
  try {
    const result = await fn()
    store.appendLog(`${label}完成。`)
    scheduleProjectSave()
    return result
  } catch (error) {
    const message = normalizeError(error)
    store.appendLog(`${label}失败：${message}`, 'error')
    ElMessage.error(message)
    throw error
  } finally {
    busy.value = false
  }
}

async function handleCreateGeometry(kind) {
  activeGeometryKind.value = kind
  viewportError.value = ''
  const handlers = {
    box: () => createBoxGeometry({ ...geometryForms.value.box }),
    sphere: () => createSphereGeometry({ ...geometryForms.value.sphere }),
    cylinder: () => createCylinderGeometry({ ...geometryForms.value.cylinder }),
  }
  const response = await runTask('geometry', '几何创建', handlers[kind])
  state.value.geometry = response
  store.resetDownstream(false)
  store.collectFiles(response)
  setViewportFromFile(findFile(response.files, 'geometry_preview.vtp'), 'geometry')
}

async function handleImportStep() {
  if (!selectedStepFile.value) {
    ElMessage.warning('请先选择 STEP / STP 文件')
    return
  }
  viewportError.value = ''
  try {
    const response = await runTask('geometry', 'STEP 导入', () => importStepGeometry(selectedStepFile.value))
    activeGeometryKind.value = 'step'
    state.value.geometry = response
    store.resetDownstream(false)
    store.collectFiles(response)
    setViewportFromFile(findFile(response.files, 'geometry_preview.vtp'), 'geometry')
  } catch (error) {
    viewportUrl.value = ''
    viewMode.value = 'geometry'
    viewportError.value = normalizeError(error)
  }
}

async function handleGenerateMesh() {
  if (!state.value.geometry?.geometry_id) {
    ElMessage.warning('请先创建或导入几何')
    return
  }
  busy.value = true
  activeTab.value = 'mesh'
  store.appendLog('网格生成任务提交。', 'message', 'mesh_start')
  try {
    const task = await startMeshTask({
      geometry_id: state.value.geometry.geometry_id,
      mesh_size: meshForm.value.mesh_size,
    })
    const response = await waitForTask(task)
    state.value.mesh = response
    store.resetDownstream(true)
    store.appendFiles(response)
    setViewportFromFile(findFile(response.files, 'mesh_preview.vtp'), 'mesh')
    if (!response.analysis_ready) {
      store.appendLog(response.analysis_message || '当前 STEP 未形成封闭实体，仅生成表面网格用于显示。', 'mesh', 'mesh_surface')
    }
    scheduleProjectSave()
  } catch (error) {
    const message = normalizeError(error)
    store.appendLog(`网格生成失败：${message}`, 'error', 'mesh_failed')
    ElMessage.error(message)
    throw error
  } finally {
    busy.value = false
  }
}

function updateLoadNodes(loadId, updater) {
  loads.value = loads.value.map((load) => (load.id === loadId ? { ...load, nodeIds: updater(load.nodeIds) } : load))
}

function invalidatePreprocess() {
  state.value.material = null
  state.value.boundary = null
  state.value.load = null
  state.value.solver = null
  state.value.summary = null
  state.value.field = null
}

function handleSelectNode({ target, nodeId }) {
  if (target === 'fixed') fixedNodeIds.value = toggleNodeId(fixedNodeIds.value, nodeId)
  if (target.startsWith('load:')) updateLoadNodes(target.slice(5), (current) => toggleNodeId(current, nodeId))
  invalidatePreprocess()
  scheduleProjectSave()
}

function handleSelectBox({ target, nodeIds }) {
  const applyBox = (current) => (selectionOperation.value === 'remove' ? removeNodeIds(current, nodeIds) : mergeNodeIds(current, nodeIds))
  if (target === 'fixed') fixedNodeIds.value = applyBox(fixedNodeIds.value)
  if (target.startsWith('load:')) updateLoadNodes(target.slice(5), applyBox)
  store.appendLog(`${target === 'fixed' ? '固定' : '载荷'}节点框选${selectionOperation.value === 'remove' ? '移除' : '追加'} ${nodeIds.length} 个。`)
  invalidatePreprocess()
  scheduleProjectSave()
}

function startSelection(payload) {
  if (!state.value.mesh?.analysis_ready) {
    ElMessage.warning(state.value.mesh?.analysis_message || '当前网格不可求解')
    return
  }
  const target = typeof payload === 'string' ? payload : payload?.target
  const loadId = payload?.loadId
  viewMode.value = 'mesh'
  if (target === 'load') {
    activeLoadId.value = loadId || activeLoadId.value
    selectionTarget.value = `load:${activeLoadId.value}`
  } else {
    selectionTarget.value = 'fixed'
  }
  selectionActive.value = true
  store.appendLog(`${target === 'fixed' ? '固定' : '载荷'}节点选择开始。`)
}

function stopSelection() {
  selectionActive.value = false
  selectionTarget.value = 'none'
  store.appendLog('节点选择结束。')
  scheduleProjectSave()
}

function clearSelection(payload) {
  const target = typeof payload === 'string' ? payload : payload?.target
  if (target === 'fixed') fixedNodeIds.value = []
  if (target === 'load') updateLoadNodes(payload.loadId, () => [])
  invalidatePreprocess()
  scheduleProjectSave()
}

function updateLoad(load) {
  loads.value = loads.value.map((item) => (item.id === load.id ? { ...item, ...load, magnitude: Number(load.magnitude ?? 0) } : item))
  activeLoadId.value = load.id
  invalidatePreprocess()
  scheduleProjectSave()
}

function addLoad() {
  const previous = activeLoad.value
  const item = createLoadItem(loads.value.length + 1)
  item.direction = previous?.direction || 'z'
  item.magnitude = previous?.magnitude ?? -1000
  loads.value = [...loads.value, item]
  activeLoadId.value = item.id
  invalidatePreprocess()
  scheduleProjectSave()
}

function removeLoad(loadId) {
  if (loads.value.length <= 1) return
  const wasSelectingRemovedLoad = selectionTarget.value === `load:${loadId}`
  loads.value = loads.value.filter((item) => item.id !== loadId)
  if (activeLoadId.value === loadId) activeLoadId.value = loads.value[0]?.id || ''
  if (wasSelectingRemovedLoad) stopSelection()
  invalidatePreprocess()
  scheduleProjectSave()
}

function copyLoadNodes({ fromId, toId }) {
  const source = loads.value.find((item) => item.id === fromId)
  if (!source) return
  updateLoadNodes(toId, () => [...source.nodeIds])
  activeLoadId.value = toId
  invalidatePreprocess()
  scheduleProjectSave()
}

async function handleApplyPreprocess() {
  if (!state.value.mesh?.mesh_id) {
    ElMessage.warning('请先生成网格')
    return
  }
  if (!state.value.mesh.analysis_ready) {
    ElMessage.warning(state.value.mesh.analysis_message || '当前网格不可求解')
    return
  }
  if (!fixedNodeIds.value.length) {
    ElMessage.warning('请先选择固定节点集')
    return
  }
  const invalidLoad = loads.value.find((load) => !load.nodeIds.length)
  if (invalidLoad) {
    ElMessage.warning(`请先为 ${invalidLoad.name || '载荷'} 选择节点集`)
    return
  }
  await runTask('load', '前处理保存', async () => {
    state.value.material = await setMaterial({ mesh_id: state.value.mesh.mesh_id, ...materialForm.value })
    state.value.boundary = await setBoundary({ mesh_id: state.value.mesh.mesh_id, node_ids: fixedNodeIds.value, dofs: [1, 2, 3] })
    state.value.load = await setLoad({
      mesh_id: state.value.mesh.mesh_id,
      loads: loads.value.map((load) => ({
        id: load.id,
        name: load.name,
        node_ids: load.nodeIds,
        direction: load.direction,
        magnitude: Number(load.magnitude ?? 0),
      })),
    })
    store.appendFiles(state.value.material)
    store.appendFiles(state.value.boundary)
    store.appendFiles(state.value.load)
    return state.value.load
  })
}

async function handleRunSolve() {
  if (!state.value.mesh?.mesh_id) {
    ElMessage.warning('请先生成网格')
    return
  }
  if (!state.value.mesh.analysis_ready) {
    ElMessage.warning(state.value.mesh.analysis_message || '当前网格不可求解')
    return
  }
  if (!selectedSolverPluginId.value) {
    ElMessage.warning('请先选择求解器')
    return
  }
  await handleApplyPreprocess()
  if (!state.value.material || !state.value.boundary || !state.value.load) return
  resetViewportToMesh()
  solving.value = true
  activeTab.value = 'solve'
  const selectedPlugin = solverPlugins.value.find((plugin) => plugin.id === selectedSolverPluginId.value)
  const solverName = selectedPlugin?.name || selectedSolverPluginId.value
  store.appendLog(`${solverName} 求解任务提交。`, 'message', 'solver_start')
  try {
    const task = await startSolverTask({
      solver_plugin_id: selectedSolverPluginId.value,
      mesh_id: state.value.mesh.mesh_id,
      material_id: state.value.material.material_id,
      boundary_id: state.value.boundary.boundary_id,
      load_id: state.value.load.load_id,
    })
    state.value.solver = await waitForTask(task)
    store.appendFiles(state.value.solver)
    state.value.summary = await getResultSummary(state.value.solver.result_id)
    store.appendFiles(state.value.summary)
    await handleFieldChange(currentField.value)
    activeTab.value = 'result'
    store.appendLog(`${solverName} 求解和结果读取完成。`, 'solver', 'solver_done')
    scheduleProjectSave()
  } catch (error) {
    const message = normalizeError(error)
    resetViewportToMesh()
    store.appendLog(`求解失败：${message}`, 'error', 'solver_failed')
    ElMessage.error(message)
  } finally {
    solving.value = false
  }
}

async function handleFieldChange(field) {
  if (!state.value.solver?.result_id) return
  selectionActive.value = false
  selectionTarget.value = 'none'
  currentField.value = field
  const response = await getResultField(state.value.solver.result_id, field)
  state.value.field = response
  setViewportFromFile(response.file, 'result', field)
  store.appendLog(`${field === 'von_mises' ? 'Von Mises 应力' : '位移'}云图已加载。`)
  scheduleProjectSave()
}

function handleExport() {
  goToTab('file', false)
}

watch(
  () => activeTab.value,
  (tabKey) => {
    if (guardingTabChange) return
    if (!workflowAccess.value[tabKey]?.enabled) {
      const previous = lastActiveTab.value
      guardingTabChange = true
      activeTab.value = workflowAccess.value[previous]?.enabled ? previous : 'geometry'
      guardingTabChange = false
      ElMessage.warning(workflowAccess.value[tabKey]?.message || '请先完成前置流程')
      return
    }
    lastActiveTab.value = tabKey
  },
)

watch(
  () => [activeTab.value, showEdges.value, showPoints.value, currentField.value],
  () => scheduleProjectSave(),
)

onMounted(() => {
  Promise.all([loadProjects(), loadSolverPlugins()]).catch((error) => {
    ElMessage.error(normalizeError(error))
  })
})
</script>

<template>
  <div class="app-shell">
    <ProjectSidebar
      :projects="projects"
      :current-project-id="currentProject?.project_id || ''"
      @create-project="handleCreateProject"
      @open-project="openProject"
      @project-command="handleProjectMenuCommand"
    />

    <section class="main-area">
      <WorkbenchTopbar
        :status-text="statusText"
        :current-case-id="currentCaseId"
        :current-case-name="currentCaseName"
        @new-case="handleNewCase"
      />

      <WorkbenchTabbar
        :active-tab="activeTab"
        :tabs="tabs"
        :workflow-access="workflowAccess"
        :show-edges="showEdges"
        :show-points="showPoints"
        :before-leave="beforeTabLeave"
        @update:active-tab="activeTab = $event"
        @update:show-edges="showEdges = $event"
        @update:show-points="showPoints = $event"
        @reset-camera="viewportRef?.resetCamera()"
        @export="handleExport"
      />

      <main class="workspace">
        <WorkbenchViewportPane
          ref="viewportRef"
          :source-url="viewportUrl"
          :view-mode="viewMode"
          :scalar-field="viewMode === 'result' ? currentField : ''"
          :show-edges="showEdges"
          :show-points="showPoints"
          :title="viewportTitle"
          :subtitle="viewportSubtitle"
          :selection-target="selectionTarget"
          :selection-active="selectionActive"
          :fixed-node-ids="fixedNodeIds"
          :load-selections="loads"
          :active-load-id="activeLoadId"
          :empty-title="viewportError ? '几何预览生成失败' : '等待几何或结果文件'"
          :empty-detail="viewportError || '创建几何或导入 STEP 后显示预览'"
          :footer-hint="selectionActive ? '节点选择中' : '视口可旋转/缩放/中键平移'"
          @error="(error) => store.appendLog(`VTK 读取失败：${normalizeError(error)}`, 'error')"
          @select-node="handleSelectNode"
          @select-box="handleSelectBox"
        />

        <WorkbenchRightPanel
          :active-tab="activeTab"
          :state="state"
          :active-geometry-kind="activeGeometryKind"
          :active-geometry-form="activeGeometryForm"
          :selected-step-file="selectedStepFile"
          :busy="busy"
          :solving="solving"
          :next-tab-label="nextTabLabel"
          :can-go-next="canGoNext"
          :next-blocked-message="nextBlockedMessage"
          :mesh-form="meshForm"
          :material-form="materialForm"
          :fixed-node-ids="fixedNodeIds"
          :loads="loads"
          :active-load-id="activeLoadId"
          :selection-target="selectionTarget"
          :selection-active="selectionActive"
          :selection-operation="selectionOperation"
          :analysis-ready="analysisReady"
          :analysis-message="analysisMessage"
          :current-field="currentField"
          :selected-solver-plugin-id="selectedSolverPluginId"
          :solver-plugins="solverPlugins"
          @update:kind="activeGeometryKind = $event"
          @update:geometry-form="(value) => Object.assign(geometryForms[editableGeometryKind], value)"
          @file-change="selectedStepFile = $event"
          @create-geometry="handleCreateGeometry"
          @import-step="handleImportStep"
          @next="goNext"
          @update:mesh-form="(value) => Object.assign(meshForm, value)"
          @generate-mesh="handleGenerateMesh"
          @update:material-form="(value) => Object.assign(materialForm, value)"
          @update-load="updateLoad"
          @add-load="addLoad"
          @remove-load="removeLoad"
          @copy-load-nodes="copyLoadNodes"
          @update:selection-operation="selectionOperation = $event"
          @start-selection="startSelection"
          @stop-selection="stopSelection"
          @clear-selection="clearSelection"
          @apply-preprocess="handleApplyPreprocess"
          @run-solve="handleRunSolve"
          @field-change="handleFieldChange"
          @solver-change="selectedSolverPluginId = $event"
        />
      </main>

      <StatusLog :logs="logs" :task="activeTask" />
    </section>
  </div>
</template>

<style scoped>
.app-shell {
  display: grid;
  grid-template-columns: 248px minmax(0, 1fr);
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  background: #eef3f8;
}

.project-rail {
  display: grid;
  grid-template-rows: auto auto minmax(0, 1fr);
  min-width: 0;
  min-height: 0;
  border-right: 1px solid var(--cae-line);
  background: #f8fbff;
}

.brand-block {
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 72px;
  padding: 0 18px;
  border-bottom: 1px solid var(--cae-line);
}

.product-mark {
  width: 38px;
  height: 38px;
  object-fit: contain;
}

.brand-block strong {
  color: #123a78;
  font-family: "DengXian", "Microsoft YaHei UI", "Microsoft YaHei", sans-serif;
  font-size: 24px;
  font-weight: 800;
}

.project-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 12px 14px;
  color: var(--cae-muted);
  font-size: 12px;
}

.project-list {
  display: grid;
  align-content: start;
  gap: 8px;
  min-height: 0;
  overflow: auto;
  padding: 0 10px 12px;
}

.project-item {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 28px;
  align-items: center;
  gap: 8px;
  min-height: 58px;
  padding: 8px 8px 8px 10px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--cae-ink);
  text-align: left;
}

.project-item:hover,
.project-item.active {
  border-color: #bed0e7;
  background: #fff;
}

.project-item.active {
  box-shadow: inset 3px 0 0 var(--cae-blue-600);
}

.project-open {
  display: block;
  min-width: 0;
  padding: 0;
  border: 0;
  background: transparent;
  color: inherit;
  text-align: left;
  cursor: pointer;
}

.project-open strong,
.project-open em {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.project-open strong {
  font-size: 13px;
}

.project-open em {
  margin-top: 4px;
  color: var(--cae-muted);
  font-size: 11px;
  font-style: normal;
}

.project-menu {
  width: 28px;
  height: 28px;
  padding: 0;
}

.main-area {
  display: grid;
  grid-template-rows: 64px 50px minmax(0, 1fr) 190px;
  min-width: 0;
  min-height: 0;
}

.topbar,
.tabbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  min-width: 0;
  padding: 0 18px;
  border-bottom: 1px solid var(--cae-line);
  background: #fff;
}

.top-meta {
  display: flex;
  align-items: center;
  gap: 28px;
  min-width: 0;
}

.top-meta > div {
  min-width: 120px;
}

.meta-label {
  display: block;
  margin-bottom: 3px;
  color: var(--cae-muted);
  font-size: 11px;
}

.top-meta strong {
  display: block;
  overflow: hidden;
  max-width: 220px;
  color: var(--cae-ink);
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.work-tabs {
  min-width: 0;
}

.work-tabs :deep(.el-tabs__header) {
  margin: 0;
}

.work-tabs :deep(.el-tabs__nav-wrap::after) {
  display: none;
}

.tab-label.locked {
  color: #9ba7b7;
  cursor: not-allowed;
}

.viewport-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  white-space: nowrap;
}

.workspace {
  display: grid;
  grid-template-columns: minmax(520px, 1fr) 380px;
  gap: 10px;
  min-height: 0;
  padding: 10px 12px 8px;
}

.center-workspace {
  display: grid;
  grid-template-rows: minmax(0, 1fr) 38px;
  min-width: 0;
  min-height: 0;
}

.viewport-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 0 12px;
  border: 1px solid var(--cae-line);
  border-top: 0;
  background: #fff;
  color: var(--cae-muted);
  font-size: 12px;
}

.right-panel {
  min-width: 0;
  min-height: 0;
  overflow: auto;
  border: 1px solid var(--cae-line);
  background: #fff;
}

@media (max-width: 1180px) {
  .app-shell {
    grid-template-columns: 1fr;
    overflow: auto;
  }

  :deep(.project-rail) {
    display: none;
  }

  .main-area {
    min-height: 100vh;
  }

  .workspace {
    grid-template-columns: 1fr;
  }

  .center-workspace {
    min-height: 580px;
  }
}
</style>
