<script setup>
import { ArrowRight, VideoPlay } from '@element-plus/icons-vue'

const props = defineProps({
  mode: {
    type: String,
    default: 'result',
  },
  summary: {
    type: Object,
    default: null,
  },
  field: {
    type: String,
    default: 'displacement',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  solving: {
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
  solverPluginId: {
    type: String,
    default: '',
  },
  solverPlugins: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['run', 'field-change', 'next', 'solver-change'])

const options = [
  { label: '位移', value: 'displacement' },
  { label: 'Von Mises', value: 'von_mises' },
]
</script>

<template>
  <section class="panel-section">
    <div class="section-head">
      <h3>{{ props.mode === 'solve' ? '求解' : '结果' }}</h3>
      <span>{{ props.mode === 'solve' ? 'Solve' : 'Result' }}</span>
    </div>

    <el-button
      class="run-button"
      type="primary"
      :icon="VideoPlay"
      :loading="props.solving"
      :disabled="props.disabled || !props.analysisReady"
      @click="emit('run')"
    >
      开始求解
    </el-button>

    <div v-if="props.mode === 'solve'" class="solver-picker">
      <span>求解器</span>
      <el-select
        :model-value="props.solverPluginId"
        placeholder="请选择求解器"
        :disabled="props.disabled || props.solving"
        @update:model-value="(value) => emit('solver-change', value)"
      >
        <el-option
          v-for="plugin in props.solverPlugins"
          :key="plugin.id"
          :label="`${plugin.name} ${plugin.version}`"
          :value="plugin.id"
        />
      </el-select>
    </div>

    <div v-if="!props.analysisReady" class="solve-blocker">
      {{ props.analysisMessage || '当前网格未形成可求解实体' }}
    </div>

    <div v-if="props.mode !== 'solve'" class="result-switch">
      <el-segmented
        :model-value="props.field"
        :options="options"
        :disabled="!props.summary"
        @update:model-value="(value) => emit('field-change', value)"
      />
    </div>

    <div v-if="props.mode !== 'solve'" class="result-list">
      <div class="result-row">
        <span>最大位移</span>
        <strong>{{ props.summary ? props.summary.max_displacement.toExponential(3) : '--' }}</strong>
        <em>mm</em>
      </div>
      <div class="result-row">
        <span>最大 Von Mises</span>
        <strong>{{ props.summary ? props.summary.max_von_mises.toExponential(3) : '--' }}</strong>
        <em>MPa</em>
      </div>
    </div>

    <div v-if="props.mode !== 'solve' && props.summary?.warnings?.length" class="result-warning">
      <strong>结果可信度提示</strong>
      <span v-for="warning in props.summary.warnings" :key="warning">{{ warning }}</span>
    </div>

    <div v-if="props.mode === 'solve'" class="panel-next">
      <span>{{ props.nextDisabled ? props.nextDisabledMessage : `下一步：${props.nextLabel}` }}</span>
      <el-button type="primary" :icon="ArrowRight" :disabled="props.nextDisabled" circle title="下一步" @click="emit('next')" />
    </div>
  </section>
</template>

<style scoped>
.panel-section {
  display: grid;
  gap: 12px;
  padding: 16px;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-head h3 {
  margin: 0;
  font-size: 15px;
}

.section-head span {
  color: var(--cae-muted);
  font-size: 11px;
  text-transform: uppercase;
}

.run-button {
  width: 100%;
}

.solve-blocker {
  padding: 8px;
  border: 1px solid #ead19c;
  background: #fff7e8;
  color: var(--cae-warn);
  font-size: 12px;
  line-height: 1.45;
}

.solver-picker {
  display: grid;
  gap: 6px;
}

.solver-picker span {
  color: var(--cae-muted);
  font-size: 12px;
}

.result-switch {
  margin-top: -2px;
}

.result-switch :deep(.el-segmented) {
  width: 100%;
}

.result-list {
  display: grid;
  gap: 8px;
}

.result-warning {
  display: grid;
  gap: 6px;
  padding: 10px 12px;
  border: 1px solid #f1c37a;
  background: #fff7e8;
  color: #8a5800;
  font-size: 12px;
  line-height: 1.45;
}

.result-warning strong {
  color: #7a4700;
  font-size: 12px;
}

.result-row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 2px 8px;
  padding: 8px 0;
  border-bottom: 1px solid #e7edf6;
}

.result-row span {
  color: var(--cae-muted);
  font-size: 12px;
}

.result-row strong {
  color: var(--cae-blue-800);
  font-size: 16px;
}

.result-row em {
  grid-column: 1 / -1;
  color: var(--cae-muted);
  font-size: 11px;
  font-style: normal;
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
