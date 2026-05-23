<script setup>
import { Plus } from '@element-plus/icons-vue'

defineProps({
  statusText: {
    type: String,
    default: '',
  },
  currentCaseId: {
    type: String,
    default: '--',
  },
  currentCaseName: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['new-case'])
</script>

<template>
  <header class="topbar">
    <div class="top-meta">
      <div>
        <span class="meta-label">求解状态</span>
        <strong>{{ statusText }}</strong>
      </div>
      <div>
        <span class="meta-label">当前算例</span>
        <strong>{{ currentCaseId }}</strong>
      </div>
      <div>
        <span class="meta-label">算例名称</span>
        <strong>{{ currentCaseName }}</strong>
      </div>
    </div>
    <el-button type="primary" plain :icon="Plus" @click="emit('new-case')">新建算例</el-button>
  </header>
</template>

<style scoped>
.topbar {
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
</style>
