<script setup>
import { FolderAdd, MoreFilled } from '@element-plus/icons-vue'

defineProps({
  projects: {
    type: Array,
    default: () => [],
  },
  currentProjectId: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['create-project', 'open-project', 'project-command'])
</script>

<template>
  <aside class="project-rail">
    <div class="brand-block">
      <img class="product-mark" src="/image.png" alt="YiYaoFlow" />
      <strong>YiYaoFlow</strong>
    </div>

    <div class="project-toolbar">
      <span>算例</span>
      <el-button size="small" type="primary" :icon="FolderAdd" @click="emit('create-project')">新建</el-button>
    </div>

    <div class="project-list">
      <div
        v-for="project in projects"
        :key="project.project_id"
        class="project-item"
        :class="{ active: currentProjectId === project.project_id }"
      >
        <button class="project-open" type="button" @click="emit('open-project', project.project_id)">
          <strong>{{ project.name }}</strong>
          <em>{{ project.case_id || '空算例' }}</em>
        </button>
        <el-dropdown trigger="click" @command="(command) => emit('project-command', command, project)">
          <el-button class="project-menu" text :icon="MoreFilled" @click.stop />
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="rename">重命名</el-dropdown-item>
              <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
  </aside>
</template>

<style scoped>
.project-rail {
  display: grid;
  grid-template-rows: auto auto minmax(0, 1fr);
  min-width: 0;
  min-height: 0;
  border-right: 1px solid var(--cae-line);
  background: #f8fbff;
}

.brand-block {
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 72px;
  padding: 0 18px;
  border-bottom: 1px solid var(--cae-line);
}

.product-mark {
  width: 38px;
  height: 38px;
  object-fit: contain;
}

.brand-block strong {
  color: #123a78;
  font-family: "DengXian", "Microsoft YaHei UI", "Microsoft YaHei", sans-serif;
  font-size: 24px;
  font-weight: 800;
}

.project-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 12px 14px;
  color: var(--cae-muted);
  font-size: 12px;
}

.project-list {
  display: grid;
  align-content: start;
  gap: 8px;
  min-height: 0;
  overflow: auto;
  padding: 0 10px 12px;
}

.project-item {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 28px;
  align-items: center;
  gap: 8px;
  min-height: 58px;
  padding: 8px 8px 8px 10px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--cae-ink);
  text-align: left;
}

.project-item:hover,
.project-item.active {
  border-color: #bed0e7;
  background: #fff;
}

.project-item.active {
  box-shadow: inset 3px 0 0 var(--cae-blue-600);
}

.project-open {
  display: block;
  min-width: 0;
  padding: 0;
  border: 0;
  background: transparent;
  color: inherit;
  text-align: left;
  cursor: pointer;
}

.project-open strong,
.project-open em {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.project-open strong {
  font-size: 13px;
}

.project-open em {
  margin-top: 4px;
  color: var(--cae-muted);
  font-size: 11px;
  font-style: normal;
}

.project-menu {
  width: 28px;
  height: 28px;
  padding: 0;
}
</style>
