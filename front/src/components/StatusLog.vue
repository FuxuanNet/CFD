<script setup>
import { computed, nextTick, ref, watch } from 'vue'

const props = defineProps({
  logs: {
    type: Array,
    default: () => [],
  },
  task: {
    type: Object,
    default: null,
  },
})

const activeTab = ref('message')
const streamRef = ref(null)
const tabs = [
  { key: 'message', label: '消息日志' },
  { key: 'mesh', label: '网格日志' },
  { key: 'solver', label: '求解日志' },
  { key: 'error', label: '错误' },
]

const taskLabel = computed(() => props.task ? `${props.task.status || 'running'} / ${props.task.phase || 'phase'} / ${props.task.progress ?? 0}%` : '日志')
const filteredLogs = computed(() => props.logs.filter((log) => (log.channel || 'message') === activeTab.value))

watch(
  () => [activeTab.value, props.logs.length],
  async () => {
    await nextTick()
    if (streamRef.value) streamRef.value.scrollTop = streamRef.value.scrollHeight
  },
)
</script>

<template>
  <footer class="status-dock">
    <div class="log-panel">
      <div class="log-head">
        <el-tabs v-model="activeTab" class="log-tabs">
          <el-tab-pane v-for="tab in tabs" :key="tab.key" :name="tab.key" :label="tab.label" />
        </el-tabs>
        <span>{{ taskLabel }}</span>
      </div>
      <div ref="streamRef" class="log-stream">
        <div v-for="log in filteredLogs" :key="log.id" class="log-line" :class="log.channel || 'message'">
          <span>[{{ log.time }}]</span>
          <em v-if="log.phase">{{ log.phase }}</em>
          <strong>{{ log.message }}</strong>
        </div>
        <div v-if="!filteredLogs.length" class="empty-log">暂无{{ tabs.find((tab) => tab.key === activeTab)?.label }}</div>
      </div>
    </div>
  </footer>
</template>

<style scoped>
.status-dock {
  display: grid;
  min-height: 0;
  padding: 8px 12px 12px;
  border-top: 1px solid var(--cae-line);
  background: #fff;
}

.log-panel {
  display: grid;
  grid-template-rows: 36px minmax(0, 1fr);
  min-width: 0;
  min-height: 0;
  border: 1px solid var(--cae-line);
  background: #fff;
}

.log-head {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  min-width: 0;
  border-bottom: 1px solid var(--cae-line);
}

.log-head > span {
  padding: 0 12px;
  color: var(--cae-muted);
  font-size: 12px;
  white-space: nowrap;
}

.log-tabs :deep(.el-tabs__header) {
  margin: 0;
  padding: 0 10px;
}

.log-tabs :deep(.el-tabs__nav-wrap::after) {
  display: none;
}

.log-stream {
  min-width: 0;
  min-height: 0;
  overflow: auto;
  padding: 8px 10px;
  font-family: Consolas, "Microsoft YaHei", monospace;
  font-size: 12px;
}

.log-line {
  display: grid;
  grid-template-columns: 86px 120px minmax(0, 1fr);
  gap: 8px;
  min-height: 22px;
  align-items: start;
  color: var(--cae-muted);
}

.log-line span {
  color: #7b8795;
}

.log-line em {
  overflow: hidden;
  color: var(--cae-blue-600);
  font-style: normal;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.log-line strong {
  color: var(--cae-ink);
  font-weight: 500;
  line-height: 1.5;
}

.log-line.error strong,
.log-line.error em {
  color: var(--cae-danger);
}

.empty-log {
  color: #98a6b8;
}
</style>
