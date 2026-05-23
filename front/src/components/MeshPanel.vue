<script setup>
import { ArrowRight, Grid } from '@element-plus/icons-vue'

defineProps({
  modelValue: {
    type: Object,
    required: true,
  },
  disabled: {
    type: Boolean,
    default: false,
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

const emit = defineEmits(['update:modelValue', 'generate', 'next'])
</script>

<template>
  <section class="panel-section">
    <div class="section-head">
      <h3>网格</h3>
      <span>Mesh</span>
    </div>

    <el-form label-position="top" size="small" :disabled="disabled">
      <el-form-item label="全局网格尺寸 mm">
        <el-input-number
          :model-value="modelValue.mesh_size"
          :min="0.2"
          :step="0.5"
          controls-position="right"
          @update:model-value="(value) => emit('update:modelValue', { ...modelValue, mesh_size: value })"
        />
      </el-form-item>

      <el-button type="primary" plain :icon="Grid" @click="emit('generate')">生成网格</el-button>
    </el-form>

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

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
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
