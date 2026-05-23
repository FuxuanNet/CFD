<script setup>
import { computed } from 'vue'
import { ArrowRight, CirclePlus, CopyDocument, Delete, EditPen, Finished, Mouse, Setting } from '@element-plus/icons-vue'

const props = defineProps({
  fixedCount: {
    type: Number,
    default: 0,
  },
  loads: {
    type: Array,
    default: () => [],
  },
  activeLoadId: {
    type: String,
    default: '',
  },
  activeTarget: {
    type: String,
    default: 'none',
  },
  selectionActive: {
    type: Boolean,
    default: false,
  },
  selectionOperation: {
    type: String,
    default: 'append',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  analysisReady: {
    type: Boolean,
    default: true,
  },
  analysisMessage: {
    type: String,
    default: '',
  },
  nextLabel: {
    type: String,
    default: '',
  },
  nextDisabled: {
    type: Boolean,
    default: true,
  },
  nextDisabledMessage: {
    type: String,
    default: '',
  },
})

const emit = defineEmits([
  'start-selection',
  'stop-selection',
  'clear-selection',
  'update-load',
  'add-load',
  'remove-load',
  'copy-load-nodes',
  'set-selection-operation',
  'apply',
  'next',
])

const totalLoadNodes = computed(() => props.loads.reduce((sum, item) => sum + (item.nodeIds?.length || 0), 0))

const statusText = computed(() => {
  if (!props.analysisReady) return props.analysisMessage || '当前网格不可求解'
  if (props.selectionActive && props.activeTarget === 'fixed') return '正在选择固定节点'
  if (props.selectionActive && props.activeTarget.startsWith('load:')) {
    const load = props.loads.find((item) => item.id === props.activeLoadId)
    return `正在选择 ${load?.name || '载荷'} 节点`
  }
  return '选择模式未开启'
})

function isActiveLoad(loadId) {
  return props.selectionActive && props.activeTarget === `load:${loadId}`
}

function toggleFixedSelection() {
  if (props.selectionActive && props.activeTarget === 'fixed') {
    emit('stop-selection')
    return
  }
  emit('start-selection', { target: 'fixed' })
}

function toggleLoadSelection(loadId) {
  if (isActiveLoad(loadId)) {
    emit('stop-selection')
    return
  }
  emit('start-selection', { target: 'load', loadId })
}

function updateLoad(load, patch) {
  emit('update-load', { ...load, ...patch })
}
</script>

<template>
  <section class="panel-section">
    <div class="section-head">
      <h3>约束 / 载荷</h3>
      <span>Node Sets</span>
    </div>

    <el-alert
      v-if="!analysisReady"
      class="analysis-alert"
      type="warning"
      :closable="false"
      :title="statusText"
      show-icon
    />

    <div class="selection-status">
      <Mouse />
      <span>{{ statusText }}</span>
      <el-segmented
        class="operation-switch"
        size="small"
        :model-value="selectionOperation"
        :options="[
          { label: '追加', value: 'append' },
          { label: '移除', value: 'remove' },
        ]"
        :disabled="disabled || !analysisReady"
        @update:model-value="(value) => emit('set-selection-operation', value)"
      />
    </div>

    <div class="node-set-row" :class="{ active: selectionActive && activeTarget === 'fixed' }">
      <div>
        <strong>固定节点集</strong>
        <span>{{ fixedCount }} nodes</span>
      </div>
      <div class="row-actions">
        <el-button size="small" :icon="EditPen" :disabled="disabled || !analysisReady" @click="toggleFixedSelection">
          {{ selectionActive && activeTarget === 'fixed' ? '结束' : '选点' }}
        </el-button>
        <el-button size="small" :icon="Delete" :disabled="disabled || !fixedCount" @click="emit('clear-selection', { target: 'fixed' })" />
      </div>
    </div>

    <div class="load-head">
      <strong>载荷力项</strong>
      <el-button size="small" :icon="CirclePlus" :disabled="disabled || !analysisReady" @click="emit('add-load')">添加</el-button>
    </div>

    <div class="load-list">
      <div
        v-for="(load, index) in loads"
        :key="load.id"
        class="load-item"
        :class="{ active: isActiveLoad(load.id) }"
      >
        <div class="load-title">
          <el-input
            size="small"
            :model-value="load.name"
            :disabled="disabled || !analysisReady"
            @update:model-value="(value) => updateLoad(load, { name: value })"
          />
          <span>{{ load.nodeIds?.length || 0 }} nodes</span>
        </div>

        <div class="load-form-grid">
          <el-select
            size="small"
            :model-value="load.direction"
            :disabled="disabled || !analysisReady"
            @update:model-value="(value) => updateLoad(load, { direction: value })"
          >
            <el-option label="X" value="x" />
            <el-option label="Y" value="y" />
            <el-option label="Z" value="z" />
          </el-select>
          <el-input-number
            size="small"
            :model-value="load.magnitude"
            :step="100"
            controls-position="right"
            :disabled="disabled || !analysisReady"
            @update:model-value="(value) => updateLoad(load, { magnitude: value })"
          />
        </div>

        <div class="load-actions">
          <el-button size="small" :icon="EditPen" :disabled="disabled || !analysisReady" @click="toggleLoadSelection(load.id)">
            {{ isActiveLoad(load.id) ? '结束' : '选点' }}
          </el-button>
          <el-button
            size="small"
            :icon="CopyDocument"
            :disabled="disabled || !analysisReady || index === 0"
            @click="emit('copy-load-nodes', { fromId: loads[index - 1]?.id, toId: load.id })"
          >
            复用上项
          </el-button>
          <el-button size="small" :icon="Delete" :disabled="disabled || !(load.nodeIds?.length)" @click="emit('clear-selection', { target: 'load', loadId: load.id })" />
          <el-button size="small" text :disabled="disabled || loads.length <= 1" @click="emit('remove-load', load.id)">删除</el-button>
        </div>
      </div>
    </div>

    <div class="panel-actions">
      <el-button :icon="Finished" :disabled="!selectionActive" @click="emit('stop-selection')">结束选择</el-button>
      <el-button
        type="primary"
        plain
        :icon="Setting"
        :disabled="disabled || !analysisReady || !fixedCount || !loads.length || !totalLoadNodes"
        @click="emit('apply')"
      >
        保存前处理
      </el-button>
    </div>

    <div class="panel-next">
      <span>{{ nextDisabled ? nextDisabledMessage : `下一步：${nextLabel}` }}</span>
      <el-button type="primary" :icon="ArrowRight" :disabled="nextDisabled" circle title="下一步" @click="emit('next')" />
    </div>
  </section>
</template>

<style scoped>
.panel-section {
  display: grid;
  gap: 12px;
  padding: 16px;
}

.section-head,
.selection-status,
.node-set-row,
.load-head,
.load-title,
.load-actions,
.panel-actions {
  display: flex;
  align-items: center;
}

.section-head,
.node-set-row,
.load-head,
.panel-actions {
  justify-content: space-between;
}

.section-head h3 {
  margin: 0;
  font-size: 16px;
}

.section-head span,
.node-set-row span,
.load-title span {
  color: var(--cae-muted);
  font-size: 11px;
}

.analysis-alert {
  margin-bottom: 10px;
}

.selection-status {
  gap: 7px;
  min-height: 38px;
  padding: 0 8px;
  border: 1px solid var(--cae-line);
  background: var(--cae-panel-soft);
  color: var(--cae-muted);
  font-size: 12px;
}

.selection-status svg {
  width: 15px;
  color: var(--cae-blue-600);
}

.operation-switch {
  margin-left: auto;
}

.node-set-row {
  gap: 8px;
  min-height: 58px;
  padding: 10px;
  border: 1px solid var(--cae-line);
  background: #fff;
}

.node-set-row.active,
.load-item.active {
  border-color: var(--cae-blue-600);
  background: var(--cae-blue-100);
}

.node-set-row strong,
.node-set-row span {
  display: block;
}

.node-set-row strong,
.load-head strong {
  font-size: 13px;
}

.node-set-row span {
  margin-top: 3px;
}

.row-actions,
.load-actions,
.panel-actions {
  gap: 6px;
}

.load-list {
  display: grid;
  gap: 8px;
  min-height: 0;
}

.load-item {
  display: grid;
  gap: 9px;
  padding: 10px;
  border: 1px solid var(--cae-line);
  background: #fff;
}

.load-title {
  gap: 8px;
}

.load-title span {
  min-width: 68px;
  text-align: right;
}

.load-form-grid {
  display: grid;
  grid-template-columns: 84px minmax(0, 1fr);
  gap: 7px;
}

.panel-actions {
  margin-top: 2px;
}

.panel-actions .el-button {
  flex: 1;
}

.panel-next {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  min-height: 34px;
  color: var(--cae-muted);
  font-size: 12px;
}

.panel-next span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
