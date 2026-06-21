import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: () => import('@/views/HomeView.vue'),
    meta: { title: 'Inicio' },
  },
  {
    path: '/queja',
    name: 'queja',
    component: () => import('@/views/QuejaView.vue'),
    meta: { title: 'Reportar queja' },
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('@/views/DashboardView.vue'),
    meta: { title: 'Dashboard' },
  },
  {
    path: '/chat',
    name: 'chat',
    component: () => import('@/views/ChatView.vue'),
    meta: { title: 'Chat IA' },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('@/views/NotFoundView.vue'),
    meta: { title: 'No encontrado' },
  },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, _from, savedPosition) {
    if (savedPosition) return savedPosition;
    if (to.hash) return { el: to.hash, behavior: 'smooth' };
    return { top: 0 };
  },
});

router.beforeEach((to, _from, next) => {
  // Quitar trailing slash (excepto en la raíz) para evitar 404 en hosts
  // que normalizan URLs añadiendo "/".
  if (to.path !== '/' && to.path.endsWith('/')) {
    return next({
      path: to.path.slice(0, -1),
      query: to.query,
      hash: to.hash,
      replace: true,
    });
  }
  const baseTitle = 'Sentinel AcademIA';
  const pageTitle = to.meta.title as string | undefined;
  document.title = pageTitle ? `${pageTitle} | ${baseTitle}` : baseTitle;
  next();
});
