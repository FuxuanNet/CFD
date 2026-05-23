<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import '@kitware/vtk.js/Rendering/Profiles/Geometry'
import vtkDataArray from '@kitware/vtk.js/Common/Core/DataArray'
import vtkCellArray from '@kitware/vtk.js/Common/Core/CellArray'
import vtkDataSet from '@kitware/vtk.js/Common/DataModel/DataSet'
import vtkPoints from '@kitware/vtk.js/Common/Core/Points'
import vtkPolyData from '@kitware/vtk.js/Common/DataModel/PolyData'
import vtkAnnotatedCubeActor from '@kitware/vtk.js/Rendering/Core/AnnotatedCubeActor'
import vtkActor from '@kitware/vtk.js/Rendering/Core/Actor'
import vtkColorTransferFunction from '@kitware/vtk.js/Rendering/Core/ColorTransferFunction'
import vtkGenericRenderWindow from '@kitware/vtk.js/Rendering/Misc/GenericRenderWindow'
import vtkInteractorStyleManipulator from '@kitware/vtk.js/Interaction/Style/InteractorStyleManipulator'
import vtkMouseCameraTrackballPanManipulator from '@kitware/vtk.js/Interaction/Manipulators/MouseCameraTrackballPanManipulator'
import vtkMouseCameraTrackballRotateManipulator from '@kitware/vtk.js/Interaction/Manipulators/MouseCameraTrackballRotateManipulator'
import vtkMouseCameraTrackballZoomManipulator from '@kitware/vtk.js/Interaction/Manipulators/MouseCameraTrackballZoomManipulator'
import vtkMapper from '@kitware/vtk.js/Rendering/Core/Mapper'
import vtkOrientationMarkerWidget from '@kitware/vtk.js/Interaction/Widgets/OrientationMarkerWidget'
import vtkPointPicker from '@kitware/vtk.js/Rendering/Core/PointPicker'
import vtkXMLPolyDataReader from '@kitware/vtk.js/IO/XML/XMLPolyDataReader'

const props = defineProps({
  sourceUrl: {
    type: String,
    default: '',
  },
  viewMode: {
    type: String,
    default: 'geometry',
  },
  scalarField: {
    type: String,
    default: '',
  },
  showEdges: {
    type: Boolean,
    default: true,
  },
  showPoints: {
    type: Boolean,
    default: true,
  },
  title: {
    type: String,
    default: '3D 视口',
  },
  subtitle: {
    type: String,
    default: '',
  },
  selectionTarget: {
    type: String,
    default: 'none',
  },
  selectionActive: {
    type: Boolean,
    default: false,
  },
  fixedNodeIds: {
    type: Array,
    default: () => [],
  },
  loadSelections: {
    type: Array,
    default: () => [],
  },
  activeLoadId: {
    type: String,
    default: '',
  },
  emptyTitle: {
    type: String,
    default: '等待几何或结果文件',
  },
  emptyDetail: {
    type: String,
    default: '创建梁或导入 STEP 后显示预览',
  },
})

const emit = defineEmits(['loaded', 'error', 'select-node', 'select-box'])

const container = ref(null)
const loading = ref(false)
const range = ref([0, 1])
const arrayNames = ref([])
const dragging = ref(false)
const dragBox = ref(null)
const dragStart = ref(null)

let genericRenderWindow = null
let renderer = null
let renderWindow = null
let actor = null
let mapper = null
let lookupTable = null
let reader = null
let dataset = null
let pointPicker = null
let fixedActor = null
let fixedMapper = null
let loadActor = null
let loadMapper = null
let activeLoadActor = null
let activeLoadMapper = null
let orientationWidget = null
let orientationActor = null
let interactorStyle = null
let loadRequestToken = 0

const allLoadNodeIds = computed(() => {
  return Array.from(new Set(props.loadSelections.flatMap((item) => item.nodeIds || []).map((nodeId) => Number(nodeId)))).sort((a, b) => a - b)
})

const activeLoadNodeIds = computed(() => {
  const active = props.loadSelections.find((item) => item.id === props.activeLoadId)
  return active?.nodeIds || []
})

const legendTitle = computed(() => {
  if (props.scalarField === 'von_mises') return 'Von Mises / MPa'
  if (props.scalarField === 'displacement') return '位移幅值 / mm'
  if (props.viewMode === 'mesh') return '表面网格'
  return '几何预览'
})

function createLookupTable(min, max) {
  const lut = vtkColorTransferFunction.newInstance()
  const high = max > min ? max : min + 1
  lut.addRGBPoint(min, 0.04, 0.22, 0.64)
  lut.addRGBPoint(min + (high - min) * 0.36, 0.08, 0.65, 0.92)
  lut.addRGBPoint(min + (high - min) * 0.68, 0.95, 0.78, 0.18)
  lut.addRGBPoint(high, 0.82, 0.16, 0.16)
  return lut
}

function configureMapper(dataset) {
  mapper.setInputData(dataset)
  mapper.setScalarVisibility(Boolean(props.scalarField))

  if (props.scalarField) {
    const pointArray = dataset.getPointData().getArrayByName(props.scalarField)
    const cellArray = dataset.getCellData().getArrayByName(props.scalarField)
    const dataArray = pointArray || cellArray
    if (dataArray) {
      const scalarRange = dataArray.getRange(dataArray.getNumberOfComponents() > 1 ? -1 : 0)
      range.value = [scalarRange[0] ?? scalarRange.min ?? 0, scalarRange[1] ?? scalarRange.max ?? 1]
      lookupTable = createLookupTable(range.value[0], range.value[1])
      mapper.setLookupTable(lookupTable)
      mapper.setScalarRange(range.value)
      mapper.setColorModeToMapScalars()
      if (pointArray) {
        mapper.setScalarModeToUsePointFieldData()
      } else {
        mapper.setScalarModeToUseCellFieldData()
      }
      mapper.setColorByArrayName(props.scalarField)
    } else {
      mapper.setScalarVisibility(false)
      range.value = [0, 1]
    }
  } else {
    range.value = [0, 1]
  }
}

function getNodeIdAtPoint(pointId) {
  if (!dataset || pointId < 0) return null
  const pointData = dataset.getPointData()
  const nodeArray = pointData.getArrayByName('node_id')
  if (nodeArray) return Number(nodeArray.getComponent(pointId, 0))

  // Older result surfaces may only preserve original point indices.
  const originalPointIds = pointData.getArrayByName('vtkOriginalPointIds')
  if (originalPointIds) return Number(originalPointIds.getComponent(pointId, 0)) + 1

  return pointId + 1
}

function getEventDisplayPosition(event) {
  if (!container.value) return null
  const rect = container.value.getBoundingClientRect()
  const canvas = container.value.querySelector('canvas')
  const scaleX = canvas ? canvas.width / rect.width : 1
  const scaleY = canvas ? canvas.height / rect.height : 1
  const cssX = event.clientX - rect.left
  const cssY = event.clientY - rect.top
  return {
    x: cssX * scaleX,
    y: (rect.height - cssY) * scaleY,
    cssX,
    cssY,
    width: rect.width,
    height: rect.height,
    scaleX,
    scaleY,
  }
}

function getNodeIdsFromPointIds(pointIds) {
  if (!dataset || !pointIds.length) return []
  return Array.from(new Set(pointIds.map((pointId) => getNodeIdAtPoint(pointId)).filter(Boolean))).sort((a, b) => a - b)
}

async function getSelectedNodesWithHardware(box, position) {
  const view = genericRenderWindow?.getApiSpecificRenderWindow?.()
  if (!view?.getSelector || !renderer) return []
  const selector = view.getSelector()
  selector.setFieldAssociation(vtkDataSet.FieldAssociations.FIELD_ASSOCIATION_POINTS)
  selector.setCaptureZValues(false)
  const minX = Math.min(box.x1, box.x2) * position.scaleX
  const maxX = Math.max(box.x1, box.x2) * position.scaleX
  const minY = (box.height - Math.max(box.y1, box.y2)) * position.scaleY
  const maxY = (box.height - Math.min(box.y1, box.y2)) * position.scaleY
  const selections = await selector.selectAsync(renderer, minX, minY, maxX, maxY)
  const pointIds = selections.flatMap((selection) => selection.getSelectionList?.() || [])
  return getNodeIdsFromPointIds(pointIds)
}

function getSelectedNodesInsideBoxFallback(box) {
  if (!dataset || !genericRenderWindow) return []
  const view = genericRenderWindow.getApiSpecificRenderWindow()
  const points = dataset.getPoints()
  const selected = []
  const minX = Math.min(box.x1, box.x2)
  const maxX = Math.max(box.x1, box.x2)
  const minY = Math.min(box.y1, box.y2)
  const maxY = Math.max(box.y1, box.y2)
  const scaleX = box.scaleX || 1
  const scaleY = box.scaleY || 1
  for (let pointId = 0; pointId < points.getNumberOfPoints(); pointId += 1) {
    const point = points.getPoint(pointId)
    const display = view.worldToDisplay(point[0], point[1], point[2], renderer)
    const cssX = display[0] / scaleX
    const cssY = box.height - display[1] / scaleY
    if (cssX >= minX && cssX <= maxX && cssY >= minY && cssY <= maxY) {
      selected.push(getNodeIdAtPoint(pointId))
    }
  }
  return selected.filter(Boolean)
}

function buildSelectionPolyData(nodeIds) {
  const output = vtkPolyData.newInstance()
  if (!dataset || !nodeIds.length) return output

  const wanted = new Set(nodeIds.map((id) => Number(id)))
  const sourcePoints = dataset.getPoints()
  const values = []
  const verts = []
  let nextPoint = 0
  for (let pointId = 0; pointId < sourcePoints.getNumberOfPoints(); pointId += 1) {
    const nodeId = getNodeIdAtPoint(pointId)
    if (!wanted.has(nodeId)) continue
    const point = sourcePoints.getPoint(pointId)
    values.push(point[0], point[1], point[2])
    verts.push(1, nextPoint)
    nextPoint += 1
  }

  const points = vtkPoints.newInstance()
  points.setData(new Float32Array(values), 3)
  const cells = vtkCellArray.newInstance()
  cells.setData(new Uint32Array(verts))
  output.setPoints(points)
  output.setVerts(cells)
  output.getPointData().setScalars(vtkDataArray.newInstance({
    name: 'selection',
    values: new Float32Array(nextPoint).fill(1),
  }))
  return output
}

function ensureSelectionActors() {
  if (!fixedMapper) {
    fixedMapper = vtkMapper.newInstance()
    fixedActor = vtkActor.newInstance()
    fixedActor.setMapper(fixedMapper)
    fixedActor.getProperty().setRepresentationToPoints()
    fixedActor.getProperty().setPointSize(9)
    fixedActor.getProperty().setColor(0.0, 0.44, 1.0)
    fixedActor.getProperty().setOpacity(0.95)
    renderer.addActor(fixedActor)
  }
  if (!loadMapper) {
    loadMapper = vtkMapper.newInstance()
    loadActor = vtkActor.newInstance()
    loadActor.setMapper(loadMapper)
    loadActor.getProperty().setRepresentationToPoints()
    loadActor.getProperty().setPointSize(9)
    loadActor.getProperty().setColor(0.95, 0.58, 0.08)
    loadActor.getProperty().setOpacity(0.95)
    renderer.addActor(loadActor)
  }
  if (!activeLoadMapper) {
    activeLoadMapper = vtkMapper.newInstance()
    activeLoadActor = vtkActor.newInstance()
    activeLoadActor.setMapper(activeLoadMapper)
    activeLoadActor.getProperty().setRepresentationToPoints()
    activeLoadActor.getProperty().setPointSize(13)
    activeLoadActor.getProperty().setColor(0.9, 0.17, 0.05)
    activeLoadActor.getProperty().setOpacity(1)
    renderer.addActor(activeLoadActor)
  }
}

function updateSelectionActors() {
  if (!renderer || !renderWindow || !dataset) return
  ensureSelectionActors()
  fixedMapper.setInputData(buildSelectionPolyData(props.fixedNodeIds))
  loadMapper.setInputData(buildSelectionPolyData(allLoadNodeIds.value))
  activeLoadMapper.setInputData(buildSelectionPolyData(activeLoadNodeIds.value))
  fixedActor.setVisibility(Boolean(props.showPoints && props.fixedNodeIds.length))
  loadActor.setVisibility(Boolean(props.showPoints && allLoadNodeIds.value.length))
  activeLoadActor.setVisibility(Boolean(props.showPoints && activeLoadNodeIds.value.length))
  renderWindow.render()
  window.requestAnimationFrame(() => renderWindow?.render?.())
}

async function loadSource() {
  if (!renderer || !renderWindow) return
  const requestToken = ++loadRequestToken
  if (!props.sourceUrl) {
    renderer.removeAllActors()
    dataset = null
    arrayNames.value = []
    fixedActor = null
    fixedMapper = null
    loadActor = null
    loadMapper = null
    activeLoadActor = null
    activeLoadMapper = null
    renderWindow.render()
    return
  }
  loading.value = true
  try {
    renderer.removeAllActors()
    reader?.delete?.()
    mapper?.delete?.()
    actor?.delete?.()

    reader = vtkXMLPolyDataReader.newInstance()
    await reader.setUrl(props.sourceUrl, { loadData: true })
    if (requestToken !== loadRequestToken) return
    dataset = reader.getOutputData(0)
    if (!dataset?.getPointData || !dataset?.getCellData) {
      dataset = null
      arrayNames.value = []
      renderWindow.render()
      emit('error', new Error(`VTK data is empty or unavailable: ${props.sourceUrl}`))
      return
    }
    arrayNames.value = [
      ...dataset.getPointData().getArrays().map((item) => item.getName()),
      ...dataset.getCellData().getArrays().map((item) => item.getName()),
    ].filter(Boolean)

    mapper = vtkMapper.newInstance()
    configureMapper(dataset)
    actor = vtkActor.newInstance()
    actor.setMapper(mapper)
    actor.getProperty().setEdgeVisibility(props.showEdges || props.viewMode === 'mesh')
    actor.getProperty().setEdgeColor(0.04, 0.16, 0.32)
    actor.getProperty().setEdgeOpacity(props.viewMode === 'mesh' ? 0.5 : 0.25)
    actor.getProperty().setOpacity(props.viewMode === 'geometry' ? 0.92 : 1)
    actor.getProperty().setSpecular(0.15)
    actor.getProperty().setSpecularPower(12)

    renderer.addActor(actor)
    fixedActor = null
    fixedMapper = null
    loadActor = null
    loadMapper = null
    activeLoadActor = null
    activeLoadMapper = null
    if (requestToken !== loadRequestToken) return
    updateSelectionActors()
    renderer.resetCamera()
    renderWindow.render()
    emit('loaded', { range: range.value, arrays: arrayNames.value })
  } catch (error) {
    if (requestToken !== loadRequestToken) return
    dataset = null
    arrayNames.value = []
    emit('error', error)
  } finally {
    if (requestToken === loadRequestToken) {
      loading.value = false
    }
  }
}

function updateEdgeVisibility() {
  if (!actor || !renderWindow) return
  actor.getProperty().setEdgeVisibility(props.showEdges || props.viewMode === 'mesh')
  renderWindow.render()
}

function resetCamera() {
  if (!renderer || !renderWindow) return
  renderer.resetCamera()
  renderWindow.render()
}

function alignCamera(axis) {
  if (!renderer || !renderWindow || !dataset) return
  const camera = renderer.getActiveCamera()
  const center = dataset.getCenter?.() || [0, 0, 0]
  const boundsLength = dataset.getLength?.() || 100
  const distance = Math.max(boundsLength * 1.8, 1)
  const positions = {
    x: [center[0] + distance, center[1], center[2]],
    y: [center[0], center[1] + distance, center[2]],
    z: [center[0], center[1], center[2] + distance],
  }
  const viewUps = {
    x: [0, 0, 1],
    y: [0, 0, 1],
    z: [0, 1, 0],
  }
  camera.setFocalPoint(...center)
  camera.setPosition(...positions[axis])
  camera.setViewUp(...viewUps[axis])
  renderer.resetCameraClippingRange()
  orientationWidget?.updateMarkerOrientation?.()
  renderWindow.render()
}

function configureInteractor() {
  const interactor = genericRenderWindow?.getInteractor?.()
  if (!interactor) return
  interactorStyle = vtkInteractorStyleManipulator.newInstance()
  interactorStyle.addMouseManipulator(vtkMouseCameraTrackballRotateManipulator.newInstance({ button: 1 }))
  interactorStyle.addMouseManipulator(vtkMouseCameraTrackballPanManipulator.newInstance({ button: 2 }))
  interactorStyle.addMouseManipulator(vtkMouseCameraTrackballZoomManipulator.newInstance({ button: 3 }))
  interactorStyle.addMouseManipulator(vtkMouseCameraTrackballZoomManipulator.newInstance({ dragEnabled: false, scrollEnabled: true }))
  interactor.setInteractorStyle(interactorStyle)
}

function configureOrientationWidget() {
  const interactor = genericRenderWindow?.getInteractor?.()
  if (!interactor || !renderer) return
  orientationActor = vtkAnnotatedCubeActor.newInstance()
  orientationActor.setDefaultStyle({
    fontStyle: 'bold',
    fontFamily: 'Arial',
    fontColor: '#172234',
    fontSizeScale: (resolution) => resolution / 3.2,
    faceColor: '#ffffff',
    edgeThickness: 0.08,
    edgeColor: '#9eacbc',
    resolution: 360,
  })
  orientationActor.setXPlusFaceProperty({ text: '+X', faceColor: '#f7d7d7' })
  orientationActor.setXMinusFaceProperty({ text: '-X', faceColor: '#f7d7d7' })
  orientationActor.setYPlusFaceProperty({ text: '+Y', faceColor: '#d9efdf' })
  orientationActor.setYMinusFaceProperty({ text: '-Y', faceColor: '#d9efdf' })
  orientationActor.setZPlusFaceProperty({ text: '+Z', faceColor: '#dce8ff' })
  orientationActor.setZMinusFaceProperty({ text: '-Z', faceColor: '#dce8ff' })
  orientationWidget = vtkOrientationMarkerWidget.newInstance({
    actor: orientationActor,
    interactor,
    interactiveRenderer: true,
    parentRenderer: renderer,
    viewportSize: 0.13,
    minPixelSize: 82,
    maxPixelSize: 120,
  })
  orientationWidget.setViewportCorner(vtkOrientationMarkerWidget.Corners.TOP_LEFT)
  orientationWidget.setEnabled(true)
}

function updateInteractorState() {
  const interactor = genericRenderWindow?.getInteractor?.()
  if (!interactor) return
  if (props.selectionActive && props.selectionTarget !== 'none') {
    interactor.disable?.()
  } else {
    interactor.enable?.()
  }
}

function claimSelectionEvent(event) {
  event.preventDefault()
  event.stopPropagation()
}

function handlePointerDown(event) {
  if (!props.selectionActive || props.selectionTarget === 'none' || !dataset) return
  claimSelectionEvent(event)
  event.currentTarget?.setPointerCapture?.(event.pointerId)
  const position = getEventDisplayPosition(event)
  if (!position) return
  dragging.value = true
  dragStart.value = { x: position.cssX, y: position.cssY, width: position.width, height: position.height }
  dragBox.value = null
}

function handlePointerMove(event) {
  if (!dragging.value || !dragStart.value) return
  claimSelectionEvent(event)
  const position = getEventDisplayPosition(event)
  if (!position) return
  const x1 = dragStart.value.x
  const y1 = dragStart.value.y
  const x2 = position.cssX
  const y2 = position.cssY
  if (Math.abs(x2 - x1) > 3 || Math.abs(y2 - y1) > 3) {
    dragBox.value = { x1, y1, x2, y2, height: position.height }
  }
}

async function handlePointerUp(event) {
  if (!dragging.value || !props.selectionActive || props.selectionTarget === 'none') return
  claimSelectionEvent(event)
  event.currentTarget?.releasePointerCapture?.(event.pointerId)
  const position = getEventDisplayPosition(event)
  const box = dragBox.value
  dragging.value = false
  dragBox.value = null
  if (!position) return

  if (box && (Math.abs(box.x2 - box.x1) > 6 || Math.abs(box.y2 - box.y1) > 6)) {
    let nodeIds = []
    try {
      nodeIds = await getSelectedNodesWithHardware({ ...box, height: position.height }, position)
    } catch (_error) {
      nodeIds = []
    }
    if (!nodeIds.length) {
      nodeIds = getSelectedNodesInsideBoxFallback({ ...box, height: position.height, scaleX: position.scaleX, scaleY: position.scaleY })
    }
    if (nodeIds.length) emit('select-box', { target: props.selectionTarget, nodeIds })
    return
  }

  pointPicker ||= vtkPointPicker.newInstance({ tolerance: 0.025 })
  pointPicker.setPickFromList(true)
  pointPicker.initializePickList()
  pointPicker.addPickList(actor)
  pointPicker.pick([position.x, position.y, 0], renderer)
  const nodeId = getNodeIdAtPoint(pointPicker.getPointId())
  if (nodeId) emit('select-node', { target: props.selectionTarget, nodeId })
}

function handlePointerCancel(event) {
  if (!dragging.value) return
  claimSelectionEvent(event)
  event.currentTarget?.releasePointerCapture?.(event.pointerId)
  dragging.value = false
  dragBox.value = null
}

onMounted(async () => {
  await nextTick()
  genericRenderWindow = vtkGenericRenderWindow.newInstance({
    background: [0.965, 0.98, 1],
    listenWindowResize: true,
  })
  genericRenderWindow.setContainer(container.value)
  renderer = genericRenderWindow.getRenderer()
  renderWindow = genericRenderWindow.getRenderWindow()
  configureInteractor()
  configureOrientationWidget()
  genericRenderWindow.resize()
  updateInteractorState()
  await loadSource()
})

onBeforeUnmount(() => {
  renderer?.removeAllActors()
  reader?.delete?.()
  mapper?.delete?.()
  actor?.delete?.()
  fixedMapper?.delete?.()
  fixedActor?.delete?.()
  loadMapper?.delete?.()
  loadActor?.delete?.()
  activeLoadMapper?.delete?.()
  activeLoadActor?.delete?.()
  orientationWidget?.setEnabled?.(false)
  orientationActor?.delete?.()
  pointPicker?.delete?.()
  genericRenderWindow?.getInteractor?.()?.enable?.()
  genericRenderWindow?.delete?.()
})

watch(() => [props.sourceUrl, props.scalarField, props.viewMode], loadSource)
watch(() => props.showEdges, updateEdgeVisibility)
watch(() => [props.selectionActive, props.selectionTarget], updateInteractorState)
watch(() => [props.fixedNodeIds, props.loadSelections, props.activeLoadId, props.showPoints], updateSelectionActors, { deep: true })

defineExpose({ resetCamera, alignCamera })
</script>

<template>
  <section class="viewport-panel">
    <div class="viewport-header">
      <div>
        <h2>{{ title }}</h2>
        <p>{{ subtitle }}</p>
      </div>
      <div class="viewport-meta">
        <span>{{ viewMode.toUpperCase() }}</span>
        <strong>{{ arrayNames.length ? `${arrayNames.length} arrays` : 'Ready' }}</strong>
      </div>
    </div>

    <div class="vtk-shell">
      <div
        ref="container"
        class="vtk-container"
        :class="{ selecting: selectionActive && selectionTarget !== 'none' }"
        @pointerdown="handlePointerDown"
        @pointermove="handlePointerMove"
        @pointerup="handlePointerUp"
        @pointercancel="handlePointerCancel"
      ></div>
      <div v-if="!sourceUrl" class="empty-state">
        <strong>{{ emptyTitle }}</strong>
        <span>{{ emptyDetail }}</span>
      </div>
      <div v-if="loading" class="loading-state">Loading VTK...</div>
      <div
        v-if="dragBox"
        class="selection-box"
        :style="{
          left: `${Math.min(dragBox.x1, dragBox.x2)}px`,
          top: `${Math.min(dragBox.y1, dragBox.y2)}px`,
          width: `${Math.abs(dragBox.x2 - dragBox.x1)}px`,
          height: `${Math.abs(dragBox.y2 - dragBox.y1)}px`,
        }"
      ></div>
      <div class="viewport-overlay top-left">
        <span>VIEW</span>
        <strong>Iso / Surface</strong>
      </div>
      <div class="view-buttons">
        <button type="button" @click="alignCamera('x')">+X</button>
        <button type="button" @click="alignCamera('y')">+Y</button>
        <button type="button" @click="alignCamera('z')">+Z</button>
      </div>
      <div class="viewport-overlay bottom-left">
        <span>{{ legendTitle }}</span>
        <div class="legend-bar"></div>
        <div class="legend-scale">
          <strong>{{ Number(range[0]).toExponential(2) }}</strong>
          <strong>{{ Number(range[1]).toExponential(2) }}</strong>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.viewport-panel {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  min-width: 0;
  min-height: 0;
  border: 1px solid var(--cae-line);
  background: #fff;
}

.viewport-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--cae-line);
}

.viewport-header h2 {
  margin: 0;
  font-size: 18px;
  line-height: 1.2;
  font-weight: 750;
}

.viewport-header p {
  margin: 5px 0 0;
  color: var(--cae-muted);
  font-size: 12px;
}

.viewport-meta {
  min-width: 126px;
  padding-left: 14px;
  border-left: 1px solid var(--cae-line);
  text-align: right;
}

.viewport-meta span {
  display: block;
  color: var(--cae-muted);
  font-size: 11px;
}

.viewport-meta strong {
  color: var(--cae-blue-800);
  font-size: 13px;
}

.vtk-shell {
  position: relative;
  min-height: 0;
  overflow: hidden;
  background:
    linear-gradient(90deg, rgba(17, 103, 201, 0.05) 1px, transparent 1px),
    linear-gradient(rgba(17, 103, 201, 0.04) 1px, transparent 1px),
    #f7fbff;
  background-size: 28px 28px;
}

.vtk-container {
  width: 100%;
  height: 100%;
}

.vtk-container.selecting {
  cursor: crosshair;
}

.selection-box {
  position: absolute;
  border: 1px solid var(--cae-blue-600);
  background: rgba(17, 103, 201, 0.12);
  pointer-events: none;
}

.empty-state,
.loading-state {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  color: var(--cae-muted);
  pointer-events: none;
}

.empty-state {
  align-content: center;
  gap: 6px;
}

.empty-state strong {
  color: var(--cae-ink);
  font-size: 15px;
}

.empty-state span,
.loading-state {
  font-size: 12px;
}

.viewport-overlay {
  position: absolute;
  border: 1px solid rgba(10, 52, 116, 0.18);
  background: rgba(255, 255, 255, 0.86);
  backdrop-filter: blur(8px);
  color: var(--cae-ink);
}

.viewport-overlay span {
  display: block;
  color: var(--cae-muted);
  font-size: 11px;
}

.viewport-overlay strong {
  font-size: 12px;
}

.top-left {
  top: 128px;
  left: 12px;
  padding: 9px 11px;
}

.view-buttons {
  position: absolute;
  top: 12px;
  right: 12px;
  display: flex;
  gap: 6px;
}

.view-buttons button {
  min-width: 34px;
  height: 30px;
  border: 1px solid rgba(10, 52, 116, 0.18);
  background: rgba(255, 255, 255, 0.9);
  color: var(--cae-ink);
  cursor: pointer;
  font-size: 12px;
  font-weight: 700;
}

.view-buttons button:hover {
  border-color: var(--cae-blue-600);
  color: var(--cae-blue-600);
}

.bottom-left {
  bottom: 12px;
  left: 12px;
  width: 224px;
  padding: 10px 11px;
}

.legend-bar {
  height: 10px;
  margin: 8px 0 4px;
  border: 1px solid rgba(7, 31, 73, 0.18);
  background: linear-gradient(90deg, #0b46a2 0%, #14a6eb 36%, #f3c747 68%, #d12a2a 100%);
}

.legend-scale {
  display: flex;
  justify-content: space-between;
  color: var(--cae-muted);
  font-size: 11px;
}

.legend-scale strong {
  color: var(--cae-muted);
  font-size: 11px;
}

</style>
