<script setup>
import { fileUrlFromReference } from '@/api/client'

defineProps({
  files: {
    type: Array,
    default: () => [],
  },
})
</script>

<template>
  <section class="panel-section file-section">
    <div class="section-head">
      <h3>文件链路</h3>
      <span>Data</span>
    </div>

    <ol v-if="files.length" class="file-flow">
      <li v-for="file in files" :key="`${file.path}-${file.name}`">
        <a :href="fileUrlFromReference(file)" target="_blank" rel="noopener" download>{{ file.name }}</a>
        <strong>{{ file.path.split('/')[2] }}</strong>
      </li>
    </ol>
    <el-empty v-else description="暂无产物文件" :image-size="58" />
  </section>
</template>

<style scoped>
.panel-section {
  padding: 16px;
}

.file-section {
  min-height: 0;
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

.file-flow {
  display: grid;
  gap: 7px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.file-flow li {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 8px;
  min-height: 32px;
  padding: 0 9px;
  border: 1px solid var(--cae-line);
  background: #fff;
}

.file-flow a {
  overflow: hidden;
  color: var(--cae-ink);
  font-family: Consolas, "Courier New", monospace;
  font-size: 12px;
  text-decoration: none;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-flow a:hover {
  color: var(--cae-blue-600);
}

.file-flow strong {
  color: var(--cae-blue-600);
  font-size: 11px;
}
</style>
