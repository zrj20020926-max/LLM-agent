import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/message',
  },
  {
    path: '/message',
    name: 'message',
    component: () => import('../views/MessageView.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
