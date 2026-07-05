import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router';

import { useAuthStore } from '@stores/auth';
import { useToastStore } from '@stores/toast';

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@views/auth/LoginPage.vue'),
    meta: { layout: 'plain', public: true, title: '\u767b\u5f55' },
  },
  {
    path: '/onboarding',
    name: 'onboarding',
    component: () => import('@views/auth/OnboardingPage.vue'),
    meta: { layout: 'plain', public: true, title: '\u8d26\u53f7\u521d\u59cb\u5316' },
  },
  {
    path: '/logout',
    name: 'logout',
    component: () => import('@views/auth/LogoutPage.vue'),
    meta: { public: true, title: '\u9000\u51fa\u767b\u5f55' },
  },
  {
    path: '/',
    redirect: '/legal',
  },
  {
    path: '/legal',
    redirect: '/legal/sessions',
    meta: { module: 'legal' },
  },
  {
    path: '/legal/sessions',
    name: 'legal-sessions',
    component: () => import('@views/legal/LegalSessionListPage.vue'),
    meta: { module: 'legal', title: '\u5f00\u59cb\u54a8\u8be2' },
  },
  {
    path: '/legal/sessions/:id',
    name: 'legal-session-detail',
    component: () => import('@views/legal/LegalSessionPage.vue'),
    meta: { module: 'legal', title: '\u6cd5\u5f8b\u54a8\u8be2' },
  },
  {
    path: '/legal/history',
    name: 'legal-history',
    component: () => import('@views/legal/LegalHistoryPage.vue'),
    meta: { module: 'legal', title: '\u54a8\u8be2\u8bb0\u5f55' },
  },
  {
    path: '/legal/reports',
    name: 'legal-reports',
    component: () => import('@views/legal/LegalReportListPage.vue'),
    meta: { module: 'legal', title: '\u6cd5\u5f8b\u62a5\u544a' },
  },
  {
    path: '/legal/reports/:id',
    name: 'legal-report-detail',
    component: () => import('@views/legal/LegalReportView.vue'),
    meta: { module: 'legal', title: '\u62a5\u544a\u8be6\u60c5' },
  },
  {
    path: '/recruitment',
    redirect: '/recruitment/tasks',
    meta: { module: 'recruitment' },
  },
  {
    path: '/recruitment/tasks',
    name: 'recruit-tasks',
    component: () => import('@views/recruitment/RecruitTaskListPage.vue'),
    meta: { module: 'recruitment', title: '\u62db\u8058\u4efb\u52a1' },
  },
  {
    path: '/recruitment/tasks/new',
    name: 'recruit-task-new',
    component: () => import('@views/recruitment/RecruitNewTaskPage.vue'),
    meta: { module: 'recruitment', title: '\u65b0\u5efa\u5206\u6790' },
  },
  {
    path: '/recruitment/tasks/:id',
    name: 'recruit-task-detail',
    component: () => import('@views/recruitment/RecruitTaskDetailPage.vue'),
    meta: { module: 'recruitment', title: '\u4efb\u52a1\u8be6\u60c5' },
  },
  {
    path: '/recruitment/reports',
    name: 'recruit-reports',
    component: () => import('@views/recruitment/RecruitReportListPage.vue'),
    meta: { module: 'recruitment', title: '\u5339\u914d\u62a5\u544a' },
  },
  {
    path: '/recruitment/reports/:id',
    name: 'recruit-report-detail',
    component: () => import('@views/recruitment/RecruitReportView.vue'),
    meta: { module: 'recruitment', title: '\u62a5\u544a\u8be6\u60c5' },
  },
  {
    path: '/data',
    redirect: '/data/sessions',
    meta: { module: 'data' },
  },
  {
    path: '/data/sessions',
    name: 'data-sessions',
    component: () => import('@views/data/DataSessionListPage.vue'),
    meta: { module: 'data', title: '\u95ee\u6570\u5bf9\u8bdd' },
  },
  {
    path: '/data/sessions/:id',
    name: 'data-session-detail',
    component: () => import('@views/data/DataSessionPage.vue'),
    meta: { module: 'data', title: '\u6570\u636e\u95ee\u7b54' },
  },
  {
    path: '/data/history',
    name: 'data-history',
    component: () => import('@views/data/DataHistoryPage.vue'),
    meta: { module: 'data', title: '\u67e5\u8be2\u5386\u53f2' },
  },
  {
    path: '/me',
    name: 'profile',
    component: () => import('@views/profile/ProfilePage.vue'),
    meta: { title: '\u4e2a\u4eba\u4fe1\u606f' },
  },
  {
    path: '/settings/api-config',
    name: 'admin-api-config',
    component: () => import('@views/admin/ApiConfigAdminPage.vue'),
    meta: { title: 'API \u914d\u7f6e' },
  },
  {
    path: '/403',
    name: 'forbidden',
    component: () => import('@views/system/ForbiddenPage.vue'),
    meta: { public: true, title: '\u6743\u9650\u4e0d\u8db3' },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('@views/system/NotFoundPage.vue'),
    meta: { public: true, title: '\u9875\u9762\u672a\u627e\u5230' },
  },
];

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior(_to, _from, savedPosition) {
    return savedPosition ?? { top: 0 };
  },
});

router.beforeEach((to) => {
  if (to.meta.title) {
    document.title = `${String(to.meta.title)} | \u4f01\u4e1a\u667a\u80fd\u4f53`;
  }

  const auth = useAuthStore();

  if (!to.meta.public && !auth.isAuthenticated) {
    return {
      name: 'login',
      query: { redirect: to.fullPath },
    };
  }

  const requiredRole = to.meta.role as string | undefined;
  if (requiredRole && auth.role !== requiredRole) {
    const toast = useToastStore();
    toast.push({
      type: 'warning',
      message: '\u5f53\u524d\u8d26\u53f7\u65e0\u6743\u8bbf\u95ee\u8be5\u9875\u9762',
      duration: 4000,
    });
    return { name: 'forbidden' };
  }

  return true;
});

declare module 'vue-router' {
  interface RouteMeta {
    public?: boolean;
    layout?: 'plain' | 'app';
    module?: 'legal' | 'recruitment' | 'data';
    role?: 'admin' | 'user';
    title?: string;
  }
}
