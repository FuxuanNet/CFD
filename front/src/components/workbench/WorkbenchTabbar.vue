<script setup>
import { Download, View } from '@element-plus/icons-vue'

defineProps({
  activeTab: {
    type: String,
    default: 'geometry',
  },
  tabs: {
    type: Array,
    default: () => [],
  },
  workflowAccess: {
    type: Object,
    default: () => ({}),
  },
  showEdges: {
    type: Boolean,
    default: true,
  },
  showPoints: {
    type: Boolean,
    default: true,
  },
  beforeLeave: {
    type: Function,
    default: undefined,
  },
})

const emit = defineEmits(['update:active-tab', 'update:show-edges', 'update:show-points', 'reset-camera', 'export'])
</script>

<template>
  <div class="tabbar">
    <el-tabs :model-value="activeTab" class="work-tabs" :before-leave="beforeLeave" @update:model-value="emit('update:active-tab', $event)">
      <el-tab-pane v-for="tab in tabs" :key="tab.key" :name="tab.key">
        <template #label>
          <span class="tab-label" :class="{ locked: !workflowAccess[tab.key]?.enabled }">{{ tab.label }}</span>
        </template>
      </el-tab-pane>
    </el-tabs>
    <div class="viewport-actions">
      <el-checkbox :model-value="showEdges" @update:model-value="emit('update:show-edges', $event)">线框显示</el-checkbox>
      <el-checkbox :model-value="showPoints" @update:model-value="emit('update:show-points', $event)">点集显示</el-checkbox>
      <el-button size="small" :icon="View" @click="emit('reset-camera')">重置视角</el-button>
      <el-button size="small" :icon="Download" @click="emit('export')">导出</el-button>
    </div>
  </div>
</template>

<style scoped>
.tabbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  min-width: 0;
  padding: 0 18px;
  border-bottom: 1px solid var(--cae-line);
  background: #fff;
}

.work-tabs {
  min-width: 0;
}

.work-tabs :deep(.el-tabs__header) {
  margin: 0;
}

.work-tabs :deep(.el-tabs__nav-wrap::after) {
  display: none;
}

.tab-label.locked {
  color: #9ba7b7;
  cursor: not-allowed;
}

.viewport-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  white-space: nowrap;
}
</style>
