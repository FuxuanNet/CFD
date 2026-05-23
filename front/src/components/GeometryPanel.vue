<script setup>
import { computed, ref } from 'vue'
import { ArrowRight, Box, Coin, UploadFilled } from '@element-plus/icons-vue'

const props = defineProps({
  kind: {
    type: String,
    default: 'box',
  },
  modelValue: {
    type: Object,
    required: true,
  },
  selectedFile: {
    type: Object,
    default: null,
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

const emit = defineEmits(['update:kind', 'update:modelValue', 'file-change', 'create-geometry', 'import-step', 'next'])

const fileInput = ref(null)
const dragging = ref(false)

const shapeOptions = [
  { key: 'box', label: '立方体', icon: Box },
  { key: 'sphere', label: '球体', icon: Coin },
  { key: 'cylinder', label: '圆柱体', icon: Coin },
]

const activeShape = computed(() => shapeOptions.find((item) => item.key === props.kind) || shapeOptions[0])

function updateField(key, value) {
  emit('update:modelValue', { ...props.modelValue, [key]: value })
}

function chooseFile(file) {
  emit('file-change', file || null)
}

function handleFileInput(event) {
  chooseFile(event.target.files?.[0] || null)
  event.target.value = ''
}

function handleDrop(event) {
  dragging.value = false
  if (props.disabled) return
  const file = event.dataTransfer?.files?.[0]
  chooseFile(file || null)
}
</script>

<template>
  <section class="panel-section">
    <div class="section-head">
      <div>
        <h3>几何</h3>
        <span>生成 STEP 后进入统一链路</span>
      </div>
    </div>

    <div class="shape-grid">
      <button
        v-for="shape in shapeOptions"
        :key="shape.key"
        class="shape-button"
        :class="{ active: activeShape.key === shape.key }"
        type="button"
        :disabled="disabled"
        @click="emit('update:kind', shape.key)"
      >
        <component :is="shape.icon" />
        <span>{{ shape.label }}</span>
      </button>
    </div>

    <el-form class="shape-form" label-position="top" size="small" :disabled="disabled">
      <template v-if="kind === 'sphere'">
        <el-form-item label="半径 mm">
          <el-input-number :model-value="modelValue.radius" :min="0.1" :step="1" controls-position="right" @update:model-value="(value) => updateField('radius', value)" />
        </el-form-item>
      </template>
      <template v-else-if="kind === 'cylinder'">
        <div class="form-grid">
          <el-form-item label="半径 mm">
            <el-input-number :model-value="modelValue.radius" :min="0.1" :step="1" controls-position="right" @update:model-value="(value) => updateField('radius', value)" />
          </el-form-item>
          <el-form-item label="高度 mm">
            <el-input-number :model-value="modelValue.height" :min="0.1" :step="5" controls-position="right" @update:model-value="(value) => updateField('height', value)" />
          </el-form-item>
        </div>
      </template>
      <template v-else>
        <div class="form-grid three">
          <el-form-item label="长度 mm">
            <el-input-number :model-value="modelValue.length" :min="1" :step="5" controls-position="right" @update:model-value="(value) => updateField('length', value)" />
          </el-form-item>
          <el-form-item label="宽度 mm">
            <el-input-number :model-value="modelValue.width" :min="1" :step="1" controls-position="right" @update:model-value="(value) => updateField('width', value)" />
          </el-form-item>
          <el-form-item label="高度 mm">
            <el-input-number :model-value="modelValue.height" :min="1" :step="1" controls-position="right" @update:model-value="(value) => updateField('height', value)" />
          </el-form-item>
        </div>
      </template>

      <el-button class="primary-action" type="primary" :loading="disabled" @click="emit('create-geometry', kind)">
        创建{{ activeShape.label }}
      </el-button>
    </el-form>

    <div class="divider"></div>

    <button
      class="drop-zone"
      :class="{ dragging }"
      type="button"
      :disabled="disabled"
      @click="fileInput?.click()"
      @dragover.prevent="dragging = true"
      @dragleave.prevent="dragging = false"
      @drop.prevent="handleDrop"
    >
      <UploadFilled />
      <strong>{{ selectedFile?.name || '选择或拖拽 STEP / STP 文件' }}</strong>
      <span>点击打开本地文件夹，或直接拖入文件</span>
    </button>
    <input ref="fileInput" class="file-input" type="file" accept=".step,.stp,.STEP,.STP" :disabled="disabled" @change="handleFileInput" />
    <el-button class="primary-action import-action" plain :disabled="disabled || !selectedFile" @click="emit('import-step')">
      确认导入 STEP
    </el-button>

    <div class="panel-next">
      <span>{{ nextDisabled ? nextDisabledMessage : `下一步：${nextLabel}` }}</span>
      <el-button type="primary" :icon="ArrowRight" :disabled="nextDisabled" circle title="下一步" @click="emit('next')" />
    </div>
  </section>
</template>

<style scoped>
.panel-section {
  display: grid;
  gap: 14px;
  padding: 16px;
}

.section-head h3 {
  margin: 0;
  font-size: 16px;
}

.section-head span {
  display: block;
  margin-top: 4px;
  color: var(--cae-muted);
  font-size: 12px;
}

.shape-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.shape-button {
  display: grid;
  place-items: center;
  gap: 6px;
  min-height: 66px;
  border: 1px solid var(--cae-line);
  background: #fff;
  color: var(--cae-ink);
  cursor: pointer;
}

.shape-button svg {
  width: 20px;
  color: var(--cae-blue-600);
}

.shape-button span {
  font-size: 12px;
}

.shape-button.active {
  border-color: var(--cae-blue-600);
  background: var(--cae-blue-100);
}

.shape-form {
  display: grid;
  gap: 4px;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.form-grid.three {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.primary-action {
  width: 100%;
  padding: 15px;
}

.divider {
  height: 1px;
  background: var(--cae-line);
}

.drop-zone {
  display: grid;
  place-items: center;
  gap: 6px;
  min-height: 132px;
  padding: 18px;
  border: 1px dashed var(--cae-line-strong);
  background: var(--cae-panel-soft);
  color: var(--cae-muted);
  cursor: pointer;
  text-align: center;
}

.drop-zone.dragging,
.drop-zone:hover {
  border-color: var(--cae-blue-600);
  background: var(--cae-blue-100);
}

.drop-zone svg {
  width: 28px;
  color: var(--cae-blue-600);
}

.drop-zone strong {
  max-width: 100%;
  overflow: hidden;
  color: var(--cae-ink);
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.drop-zone span {
  font-size: 12px;
}

.file-input {
  display: none;
}

.import-action {
  margin-top: -4px;
}

.panel-next {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  min-height: 34px;
  margin-top: 2px;
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
