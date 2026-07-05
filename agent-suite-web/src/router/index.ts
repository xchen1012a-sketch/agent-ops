import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router';

import { useAuthStore } from '@stores/auth';
import { useToastStore } from '@stores/toast';

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@views/auth/LoginPage.vue'),
    meta: { layout: 'plain', public: true, title: '登录' },
  },
  {
    path: '/onboarding',
    name: 'onboarding',
    component: () => import('@views/auth/OnboardingPage.vue'),
    meta: { layout: 'plain', public: true, title: '账号初始化' },
  },
  {
    path: '/logout',
    name: 'logout',
    component: () => import('@views/auth/LogoutPage.vue'),
    meta: { public: true, title: '退出登录' },
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
    meta: { module: 'legal', title: '法律咨询 - 会话列表' },
  },
  {
    path: '/legal/sessions/:id',
    name: 'legal-session-detail',
    component: () => import('@views/legal/LegalSessionPage.vue'),
    meta: { module: 'legal', title: '法律咨询 - 会话' },
  },
  {
    path: '/legal/history',
    name: 'legal-history',
    component: () => import('@views/legal/LegalHistoryPage.vue'),
    meta: { module: 'legal', title: '法律咨询 - 历史搜索' },
  },
  {
    path: '/legal/reports',
    name: 'legal-reports',
    component: () => import('@views/legal/LegalReportListPage.vue'),
    meta: { module: 'legal', title: '法律咨询 - 报告' },
  },
  {
    path: '/legal/reports/:id',
    name: 'legal-report-detail',
    component: () => import('@views/legal/LegalReportView.vue'),
    meta: { module: 'legal', title: '法律咨询 - 报告详情' },
  },
  {
    path: '/legal/admin/users',
    name: 'legal-admin-users',
    component: () => import('@views/legal/admin/UserAdminPage.vue'),
    meta: { module: 'legal', role: 'admin', title: '用户管理' },
  },
  {
    path: '/legal/admin/categories',
    name: 'legal-admin-categories',
    component: () => import('@views/legal/admin/CategoryAdminPage.vue'),
    meta: { module: 'legal', role: 'admin', title: '法律分类管理' },
  },
  {
    path: '/legal/admin/knowledge',
    name: 'legal-admin-knowledge',
    component: () => import('@views/legal/admin/KnowledgeAdminPage.vue'),
    meta: { module: 'legal', role: 'admin', title: '知识材料管理' },
  },
  {
    path: '/legal/admin/prompts',
    name: 'legal-admin-prompts',
    component: () => import('@views/legal/admin/PromptAdminPage.vue'),
    meta: { module: 'legal', role: 'admin', title: 'Prompt 版本管理' },
  },
  {
    path: '/legal/admin/reviews',
    name: 'legal-admin-reviews',
    component: () => import('@views/legal/admin/HighRiskReviewAdminPage.vue'),
    meta: { module: 'legal', role: 'admin', title: '高风险审核' },
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
    meta: { module: 'recruitment', title: '智能招聘 - 任务列表' },
  },
  {
    path: '/recruitment/tasks/new',
    name: 'recruit-task-new',
    component: () => import('@views/recruitment/RecruitNewTaskPage.vue'),
    meta: { module: 'recruitment', title: '智能招聘 - 新建分析' },
  },
  {
    path: '/recruitment/tasks/:id',
    name: 'recruit-task-detail',
    component: () => import('@views/recruitment/RecruitTaskDetailPage.vue'),
    meta: { module: 'recruitment', title: '智能招聘 - 任务详情' },
  },
  {
    path: '/recruitment/materials',
    name: 'recruit-materials',
    component: () => import('@views/recruitment/RecruitMaterialListPage.vue'),
    meta: { module: 'recruitment', title: '智能招聘 - 材料' },
  },
  {
    path: '/recruitment/reports',
    name: 'recruit-reports',
    component: () => import('@views/recruitment/RecruitReportListPage.vue'),
    meta: { module: 'recruitment', title: '智能招聘 - 报告' },
  },
  {
    path: '/recruitment/admin/scoring',
    name: 'recruit-admin-scoring',
    component: () => import('@views/recruitment/admin/ScoringAdminPage.vue'),
    meta: { module: 'recruitment', role: 'admin', title: '评分规则真源' },
  },
  {
    path: '/recruitment/admin/audit',
    name: 'recruit-admin-audit',
    component: () => import('@views/recruitment/admin/AuditAdminPage.vue'),
    meta: { module: 'recruitment', role: 'admin', title: '招聘审计' },
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
    meta: { module: 'data', title: '智能问数 - 会话列表' },
  },
  {
    path: '/data/sessions/:id',
    name: 'data-session-detail',
    component: () => import('@views/data/DataSessionPage.vue'),
    meta: { module: 'data', title: '智能问数 - 对话查询' },
  },
  {
    path: '/data/history',
    name: 'data-history',
    component: () => import('@views/data/DataHistoryPage.vue'),
    meta: { module: 'data', title: '智能问数 - 查询历史' },
  },
  {
    path: '/data/admin/sql-audit',
    name: 'data-admin-sql-audit',
    component: () => import('@views/data/admin/SqlAuditPage.vue'),
    meta: { module: 'data', role: 'admin', title: 'SQL 审计' },
  },
  {
    path: '/me',
    name: 'profile',
    component: () => import('@views/profile/ProfilePage.vue'),
    meta: { title: '个人信息' },
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('@views/profile/SettingsPage.vue'),
    meta: { title: '偏好设置' },
  },
  {
    path: '/health',
    name: 'health',
    component: () => import('@views/system/HealthPage.vue'),
    meta: { public: true, title: '系统健康' },
  },
  {
    path: '/403',
    name: 'forbidden',
    component: () => import('@views/system/ForbiddenPage.vue'),
    meta: { public: true, title: '权限不足' },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('@views/system/NotFoundPage.vue'),
    meta: { public: true, title: '页面未找到' },
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
    document.title = `${String(to.meta.title)} | 企业智能体平台`;
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
      message: '当前账号无权访问该页面',
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
