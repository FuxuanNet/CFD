<script setup>
import { ref } from 'vue'

import VtkViewport from '@/components/VtkViewport.vue'

const viewportRef = ref(null)

defineProps({
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
    default: '',
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
    default: '',
  },
  emptyDetail: {
    type: String,
    default: '',
  },
  footerHint: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['error', 'select-node', 'select-box'])

function resetCamera() {
  viewportRef.value?.resetCamera?.()
}

defineExpose({ resetCamera })
</script>

<template>
  <div class="center-workspace">
    <VtkViewport
      ref="viewportRef"
      :source-url="sourceUrl"
      :view-mode="viewMode"
      :scalar-field="scalarField"
      :show-edges="showEdges"
      :show-points="showPoints"
      :title="title"
      :subtitle="subtitle"
      :selection-target="selectionTarget"
      :selection-active="selectionActive"
      :fixed-node-ids="fixedNodeIds"
      :load-selections="loadSelections"
      :active-load-id="activeLoadId"
      :empty-title="emptyTitle"
      :empty-detail="emptyDetail"
      @error="emit('error', $event)"
      @select-node="emit('select-node', $event)"
      @select-box="emit('select-box', $event)"
    />
    <div class="viewport-foot">
      <span>单位：mm-N-MPa</span>
      <span>{{ footerHint }}</span>
    </div>
  </div>
</template>

<style scoped>
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
</style>
