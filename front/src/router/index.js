import { createRouter, createWebHistory } from 'vue-router'
import CaeWorkbenchView from '@/views/CaeWorkbenchView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'cae-workbench',
      component: CaeWorkbenchView,
    },
  ],
})

export default router
