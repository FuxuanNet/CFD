<script setup>
import { ArrowRight } from '@element-plus/icons-vue'

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

const emit = defineEmits(['update:modelValue', 'next'])
</script>

<template>
  <section class="panel-section">
    <div class="section-head">
      <h3>材料</h3>
      <span>Material</span>
    </div>

    <el-form label-position="top" size="small" :disabled="disabled">
      <el-form-item label="材料名称">
        <el-input
          :model-value="modelValue.name"
          @update:model-value="(value) => emit('update:modelValue', { ...modelValue, name: value })"
        />
      </el-form-item>
      <div class="form-grid">
        <el-form-item label="弹性模量 MPa">
          <el-input-number
            :model-value="modelValue.elastic_modulus"
            :min="1"
            :step="1000"
            controls-position="right"
            @update:model-value="(value) => emit('update:modelValue', { ...modelValue, elastic_modulus: value })"
          />
        </el-form-item>
        <el-form-item label="泊松比">
          <el-input-number
            :model-value="modelValue.poisson_ratio"
            :min="0.01"
            :max="0.49"
            :step="0.01"
            controls-position="right"
            @update:model-value="(value) => emit('update:modelValue', { ...modelValue, poisson_ratio: value })"
          />
        </el-form-item>
      </div>
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

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
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
