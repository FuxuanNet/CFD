<script setup>
import BoundaryLoadPanel from '@/components/BoundaryLoadPanel.vue'
import FileFlowPanel from '@/components/FileFlowPanel.vue'
import GeometryPanel from '@/components/GeometryPanel.vue'
import MaterialPanel from '@/components/MaterialPanel.vue'
import MeshPanel from '@/components/MeshPanel.vue'
import ResultPanel from '@/components/ResultPanel.vue'

defineProps({
  activeTab: { type: String, default: 'geometry' },
  state: { type: Object, default: () => ({}) },
  activeGeometryKind: { type: String, default: 'box' },
  activeGeometryForm: { type: Object, default: () => ({}) },
  selectedStepFile: { type: Object, default: null },
  busy: { type: Boolean, default: false },
  solving: { type: Boolean, default: false },
  nextTabLabel: { type: String, default: '' },
  canGoNext: { type: Boolean, default: false },
  nextBlockedMessage: { type: String, default: '' },
  meshForm: { type: Object, default: () => ({}) },
  materialForm: { type: Object, default: () => ({}) },
  fixedNodeIds: { type: Array, default: () => [] },
  loads: { type: Array, default: () => [] },
  activeLoadId: { type: String, default: '' },
  selectionTarget: { type: String, default: 'none' },
  selectionActive: { type: Boolean, default: false },
  selectionOperation: { type: String, default: 'append' },
  analysisReady: { type: Boolean, default: true },
  analysisMessage: { type: String, default: '' },
  currentField: { type: String, default: 'displacement' },
  selectedSolverPluginId: { type: String, default: '' },
  solverPlugins: { type: Array, default: () => [] },
})

const emit = defineEmits([
  'update:kind', 'update:geometry-form', 'file-change', 'create-geometry', 'import-step', 'next',
  'update:mesh-form', 'generate-mesh', 'update:material-form', 'update-load', 'add-load', 'remove-load',
  'copy-load-nodes', 'update:selection-operation', 'start-selection', 'stop-selection', 'clear-selection',
  'apply-preprocess', 'run-solve', 'field-change', 'solver-change',
])
</script>

<template>
  <aside class="right-panel" aria-label="参数和结果">
    <FileFlowPanel v-if="activeTab === 'file'" :files="state.files" />
    <GeometryPanel
      v-else-if="activeTab === 'geometry'"
      :kind="activeGeometryKind"
      :model-value="activeGeometryForm"
      :selected-file="selectedStepFile"
      :disabled="busy || solving"
      :next-label="nextTabLabel"
      :next-disabled="!canGoNext"
      :next-disabled-message="nextBlockedMessage"
      @update:kind="emit('update:kind', $event)"
      @update:model-value="emit('update:geometry-form', $event)"
      @file-change="emit('file-change', $event)"
      @create-geometry="emit('create-geometry', $event)"
      @import-step="emit('import-step')"
      @next="emit('next')"
    />
    <MeshPanel
      v-else-if="activeTab === 'mesh'"
      :model-value="meshForm"
      :disabled="busy || solving || !state.geometry"
      :next-label="nextTabLabel"
      :next-disabled="!canGoNext"
      :next-disabled-message="nextBlockedMessage"
      @update:model-value="emit('update:mesh-form', $event)"
      @generate="emit('generate-mesh')"
      @next="emit('next')"
    />
    <MaterialPanel
      v-else-if="activeTab === 'material'"
      :model-value="materialForm"
      :disabled="busy || solving || !state.mesh"
      :next-label="nextTabLabel"
      :next-disabled="!canGoNext"
      :next-disabled-message="nextBlockedMessage"
      @update:model-value="emit('update:material-form', $event)"
      @next="emit('next')"
    />
    <BoundaryLoadPanel
      v-else-if="activeTab === 'load'"
      :fixed-count="fixedNodeIds.length"
      :loads="loads"
      :active-load-id="activeLoadId"
      :active-target="selectionTarget"
      :selection-active="selectionActive"
      :selection-operation="selectionOperation"
      :analysis-ready="analysisReady"
      :analysis-message="analysisMessage"
      :disabled="busy || solving || !state.mesh"
      :next-label="nextTabLabel"
      :next-disabled="!canGoNext"
      :next-disabled-message="nextBlockedMessage"
      @update-load="emit('update-load', $event)"
      @add-load="emit('add-load')"
      @remove-load="emit('remove-load', $event)"
      @copy-load-nodes="emit('copy-load-nodes', $event)"
      @set-selection-operation="emit('update:selection-operation', $event)"
      @start-selection="emit('start-selection', $event)"
      @stop-selection="emit('stop-selection')"
      @clear-selection="emit('clear-selection', $event)"
      @apply="emit('apply-preprocess')"
      @next="emit('next')"
    />
    <ResultPanel
      v-else
      :mode="activeTab"
      :summary="state.summary"
      :field="currentField"
      :disabled="busy || solving || !state.mesh"
      :solving="solving"
      :analysis-ready="analysisReady"
      :analysis-message="analysisMessage"
      :solver-plugin-id="selectedSolverPluginId"
      :solver-plugins="solverPlugins"
      :next-label="nextTabLabel"
      :next-disabled="!canGoNext"
      :next-disabled-message="nextBlockedMessage"
      @run="emit('run-solve')"
      @field-change="emit('field-change', $event)"
      @solver-change="emit('solver-change', $event)"
      @next="emit('next')"
    />
  </aside>
</template>

<style scoped>
.right-panel {
  min-width: 0;
  min-height: 0;
  overflow: auto;
  border: 1px solid var(--cae-line);
  background: #fff;
}
</style>
