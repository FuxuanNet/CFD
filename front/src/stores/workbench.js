import { computed, reactive, ref, toRaw } from 'vue'
import { defineStore } from 'pinia'

function createLoadItem(index = 1, nodeIds = []) {
  return {
    id: `load_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`,
    name: `F${index}`,
    direction: 'z',
    magnitude: -1000,
    nodeIds: [...nodeIds],
  }
}

function initialLogs() {
  return [
    {
      id: 1,
      time: new Date().toLocaleTimeString('zh-CN', { hour12: false }),
      channel: 'message',
      message: '系统初始化完成，等待用户创建或导入模型。',
    },
  ]
}

function clone(value) {
  return JSON.parse(JSON.stringify(toRaw(value)))
}

export const useWorkbenchStore = defineStore('workbench', () => {
  const projects = ref([])
  const currentProject = ref(null)
  const solverPlugins = ref([])
  const selectedSolverPluginId = ref('')
  const activeTab = ref('geometry')
  const activeTask = ref(null)
  const seenTaskLogs = ref(new Set())
  const busy = ref(false)
  const solving = ref(false)
  const showEdges = ref(true)
  const showPoints = ref(true)
  const currentField = ref('displacement')
  const viewMode = ref('geometry')
  const viewportUrl = ref('')
  const viewportError = ref('')
  const selectedStepFile = ref(null)
  const activeGeometryKind = ref('box')
  const fixedNodeIds = ref([])
  const loads = ref([createLoadItem(1)])
  const activeLoadId = ref(loads.value[0].id)
  const selectionTarget = ref('none')
  const selectionActive = ref(false)
  const selectionOperation = ref('append')
  const logs = ref(initialLogs())

  const geometryForms = reactive({
    box: { length: 100, width: 10, height: 10 },
    sphere: { radius: 5 },
    cylinder: { radius: 5, height: 30 },
  })
  const meshForm = reactive({ mesh_size: 5 })
  const materialForm = reactive({
    name: 'Steel',
    elastic_modulus: 210000,
    poisson_ratio: 0.3,
  })
  const state = reactive({
    geometry: null,
    mesh: null,
    material: null,
    boundary: null,
    load: null,
    solver: null,
    summary: null,
    field: null,
    files: [],
  })

  const currentCaseId = computed(() => state.geometry?.geometry_id || state.mesh?.mesh_id || state.solver?.result_id || currentProject.value?.case_id || '--')
  const activeLoad = computed(() => loads.value.find((item) => item.id === activeLoadId.value) || loads.value[0] || null)
  const totalLoadNodeCount = computed(() => loads.value.reduce((sum, item) => sum + (item.nodeIds?.length || 0), 0))
  const analysisReady = computed(() => state.mesh?.analysis_ready !== false)
  const analysisMessage = computed(() => state.mesh?.analysis_message || '')
  const statusText = computed(() => {
    if (activeTask.value && ['queued', 'running'].includes(activeTask.value.status)) return `${activeTask.value.phase} ${activeTask.value.progress}%`
    if (solving.value) return '求解中'
    if (state.summary) return '结果就绪'
    if (state.mesh && !analysisReady.value) return '仅可显示'
    if (state.mesh) return '网格完成'
    if (state.geometry) return '几何完成'
    return '准备就绪'
  })

  function appendLog(message, channel = 'message', phase = '') {
    logs.value.push({
      id: Date.now() + Math.random(),
      time: new Date().toLocaleTimeString('zh-CN', { hour12: false }),
      channel,
      phase,
      message,
    })
  }

  function appendTaskLogs(task) {
    for (const log of task?.logs || []) {
      const key = `${task.task_id}:${log.sequence}`
      if (seenTaskLogs.value.has(key)) continue
      seenTaskLogs.value.add(key)
      logs.value.push({
        id: key,
        time: log.time,
        channel: log.channel || 'message',
        phase: log.phase,
        message: log.message,
      })
    }
  }

  function resetLoadItems() {
    loads.value = [createLoadItem(1)]
    activeLoadId.value = loads.value[0].id
  }

  function resetDownstream(keepMesh = false) {
    if (!keepMesh) state.mesh = null
    state.material = null
    state.boundary = null
    state.load = null
    state.solver = null
    state.summary = null
    state.field = null
    fixedNodeIds.value = []
    resetLoadItems()
    selectionTarget.value = 'none'
    selectionActive.value = false
  }

  function resetWorkspace() {
    state.geometry = null
    state.mesh = null
    state.material = null
    state.boundary = null
    state.load = null
    state.solver = null
    state.summary = null
    state.field = null
    state.files = []
    fixedNodeIds.value = []
    resetLoadItems()
    activeTask.value = null
    seenTaskLogs.value = new Set()
    selectionTarget.value = 'none'
    selectionActive.value = false
    viewportUrl.value = ''
    viewportError.value = ''
    viewMode.value = 'geometry'
    currentField.value = 'displacement'
    showEdges.value = true
    showPoints.value = true
    activeTab.value = 'geometry'
    selectedStepFile.value = null
    logs.value = initialLogs()
  }

  function collectFiles(...responses) {
    const next = []
    for (const response of responses) {
      for (const file of response?.files || []) {
        if (!next.some((item) => item.path === file.path)) next.push(file)
      }
    }
    state.files = next
  }

  function appendFiles(response) {
    for (const file of response?.files || []) {
      if (!state.files.some((item) => item.path === file.path)) state.files.push(file)
    }
  }

  function toSnapshot() {
    return {
      state: clone(state),
      forms: {
        geometry: clone(geometryForms),
        mesh: clone(meshForm),
        material: clone(materialForm),
        activeGeometryKind: activeGeometryKind.value,
      },
      selection: {
        fixedNodeIds: clone(fixedNodeIds.value),
        loads: clone(loads.value),
        activeLoadId: activeLoadId.value,
        selectionOperation: selectionOperation.value,
        selectedSolverPluginId: selectedSolverPluginId.value,
      },
      files: clone(state.files),
      logs: clone(logs.value).slice(-120),
      view: {
        activeTab: activeTab.value,
        viewMode: viewMode.value,
        currentField: currentField.value,
        viewportUrl: viewportUrl.value,
        viewportError: viewportError.value,
        showEdges: showEdges.value,
        showPoints: showPoints.value,
      },
    }
  }

  function restoreSnapshot(snapshot = {}) {
    resetWorkspace()
    Object.assign(geometryForms.box, snapshot.forms?.geometry?.box || {})
    Object.assign(geometryForms.sphere, snapshot.forms?.geometry?.sphere || {})
    Object.assign(geometryForms.cylinder, snapshot.forms?.geometry?.cylinder || {})
    Object.assign(meshForm, snapshot.forms?.mesh || {})
    Object.assign(materialForm, snapshot.forms?.material || {})
    activeGeometryKind.value = snapshot.forms?.activeGeometryKind || 'box'
    Object.assign(state, {
      geometry: snapshot.state?.geometry || null,
      mesh: snapshot.state?.mesh || null,
      material: snapshot.state?.material || null,
      boundary: snapshot.state?.boundary || null,
      load: snapshot.state?.load || null,
      solver: snapshot.state?.solver || null,
      summary: snapshot.state?.summary || null,
      field: snapshot.state?.field || null,
      files: snapshot.files || snapshot.state?.files || [],
    })
    fixedNodeIds.value = snapshot.selection?.fixedNodeIds || []
    loads.value = snapshot.selection?.loads?.length ? snapshot.selection.loads : [createLoadItem(1)]
    activeLoadId.value = snapshot.selection?.activeLoadId || loads.value[0]?.id || ''
    selectionOperation.value = snapshot.selection?.selectionOperation || 'append'
    selectedSolverPluginId.value = snapshot.selection?.selectedSolverPluginId || selectedSolverPluginId.value || ''
    logs.value = snapshot.logs?.length ? snapshot.logs : initialLogs()
    activeTab.value = snapshot.view?.activeTab || 'geometry'
    const requestedViewMode = snapshot.view?.viewMode || (state.summary ? 'result' : state.mesh ? 'mesh' : 'geometry')
    const hasResultFile = typeof snapshot.view?.viewportUrl === 'string' && snapshot.view.viewportUrl.includes('/results/')
    viewMode.value = requestedViewMode === 'result' && (!state.summary || !hasResultFile)
      ? (state.mesh ? 'mesh' : 'geometry')
      : requestedViewMode
    currentField.value = snapshot.view?.currentField || 'displacement'
    viewportUrl.value = viewMode.value === 'result' && !hasResultFile ? '' : (snapshot.view?.viewportUrl || '')
    viewportError.value = snapshot.view?.viewportError || ''
    showEdges.value = snapshot.view?.showEdges ?? true
    showPoints.value = snapshot.view?.showPoints ?? true
  }

  return {
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
    totalLoadNodeCount,
    analysisReady,
    analysisMessage,
    statusText,
    appendLog,
    appendTaskLogs,
    resetLoadItems,
    resetDownstream,
    resetWorkspace,
    collectFiles,
    appendFiles,
    toSnapshot,
    restoreSnapshot,
  }
})
