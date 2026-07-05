<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';

import { useAuthStore } from '@stores/auth';
import { router } from '@router/index';

interface SidebarItem {
  name: string;
  label: string;
  icon: string;
  module?: 'legal' | 'recruitment' | 'data';
  role?: 'admin' | 'user';
  children?: SidebarItem[];
}

const props = defineProps<{ collapsed: boolean }>();
const emit = defineEmits<{ (e: 'toggle'): void }>();

const route = useRoute();
const auth = useAuthStore();

const groups = computed<SidebarItem[]>(() => {
  const items: SidebarItem[] = [
    {
      name: 'legal-group',
      label: '法律咨询',
      icon: 'Document',
      module: 'legal',
      children: [
        { name: 'legal-sessions', label: '会话列表', icon: 'ChatDotRound' },
        { name: 'legal-history', label: '历史搜索', icon: 'Search' },
        { name: 'legal-reports', label: '咨询报告', icon: 'Notebook' },
      ],
    },
    {
      name: 'recruit-group',
      label: '智能招聘',
      icon: 'User',
      module: 'recruitment',
      children: [
        { name: 'recruit-tasks', label: '任务列表', icon: 'List' },
        { name: 'recruit-task-new', label: '新建分析', icon: 'Plus' },
        { name: 'recruit-materials', label: '材料管理', icon: 'Folder' },
        { name: 'recruit-reports', label: '匹配报告', icon: 'DataAnalysis' },
      ],
    },
    {
      name: 'data-group',
      label: '智能问数',
      icon: 'Histogram',
      module: 'data',
      children: [
        { name: 'data-sessions', label: '会话列表', icon: 'ChatDotRound' },
        { name: 'data-history', label: '查询历史', icon: 'Search' },
      ],
    },
  ];

  if (auth.isAdmin) {
    items.push({
      name: 'admin-group',
      label: '系统管理',
      icon: 'Setting',
      children: [
        { name: 'legal-admin-knowledge', label: '知识材料', icon: 'Files', role: 'admin' },
        { name: 'legal-admin-categories', label: '法律分类', icon: 'Collection', role: 'admin' },
        { name: 'legal-admin-users', label: '用户管理', icon: 'UserFilled', role: 'admin' },
        { name: 'legal-admin-prompts', label: 'Prompt 版本', icon: 'Document', role: 'admin' },
        { name: 'recruit-admin-scoring', label: '评分规则', icon: 'TrendCharts', role: 'admin' },
        { name: 'recruit-admin-audit', label: '招聘审计', icon: 'View', role: 'admin' },
        { name: 'data-admin-sql-audit', label: 'SQL 审计', icon: 'Monitor', role: 'admin' },
      ],
    });
  }

  return items;
});

const activeModule = computed(() => (route.meta?.module ?? null) as string | null);

function navigate(name: string): void {
  void router.push({ name });
}

function isActive(item: SidebarItem): boolean {
  if (item.children) {
    return item.children.some((child) => route.name?.toString().startsWith(child.name));
  }
  return route.name === item.name;
}
</script>

<template>
  <aside
    class="app-sidebar"
    :class="{ 'app-sidebar--collapsed': props.collapsed }"
    aria-label="主导航"
  >
    <nav class="app-sidebar__nav" role="navigation">
      <template v-for="group in groups" :key="group.name">
        <button
          type="button"
          class="app-sidebar__group-title"
          :class="{ 'is-active-module': group.module === activeModule }"
          :title="group.label"
          @click="navigate(group.children?.[0]?.name ?? group.name)"
        >
          <el-icon class="app-sidebar__group-icon">
            <component :is="group.icon" />
          </el-icon>
          <span v-if="!props.collapsed" class="app-sidebar__group-label">{{ group.label }}</span>
        </button>
        <ul v-if="!props.collapsed && group.children" class="app-sidebar__sublist">
          <li v-for="child in group.children" :key="child.name">
            <button
              type="button"
              class="app-sidebar__sublink"
              :class="{ 'is-active': isActive(child) }"
              :title="child.label"
              @click="navigate(child.name)"
            >
              <el-icon class="app-sidebar__sublink-icon">
                <component :is="child.icon" />
              </el-icon>
              <span>{{ child.label }}</span>
            </button>
          </li>
        </ul>
      </template>
    </nav>
    <button
      type="button"
      class="app-sidebar__toggle"
      :aria-label="props.collapsed ? '展开侧边栏' : '收起侧边栏'"
      :aria-expanded="!props.collapsed"
      @click="emit('toggle')"
    >
      <el-icon><component :is="props.collapsed ? 'Expand' : 'Fold'" /></el-icon>
    </button>
  </aside>
</template>

<style scoped>
.app-sidebar {
  display: flex;
  flex-direction: column;
  background-color: var(--color-surface);
  border-right: 1px solid var(--color-border);
  transition:
    width var(--duration-normal) var(--ease-in-out),
    transform var(--duration-normal) var(--ease-in-out);
}

.app-sidebar__nav {
  flex: 1 1 auto;
  padding: var(--space-3);
  overflow-y: auto;
}

.app-sidebar__group-title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  width: 100%;
  padding: var(--space-2) var(--space-3);
  margin-bottom: var(--space-1);
  border: none;
  background-color: transparent;
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  font-weight: 600;
  cursor: pointer;
  transition:
    background-color var(--duration-fast) var(--ease-in-out),
    color var(--duration-fast) var(--ease-in-out);
}

.app-sidebar__group-title:hover,
.app-sidebar__group-title.is-active-module {
  background-color: var(--color-surface-muted);
  color: var(--color-text);
}

.app-sidebar__group-icon {
  flex: 0 0 auto;
}

.app-sidebar__sublist {
  list-style: none;
  margin: 0 0 var(--space-2);
  padding: 0;
}

.app-sidebar__sublink {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  width: 100%;
  padding: var(--space-2) var(--space-3) var(--space-2) var(--space-8);
  border: none;
  background-color: transparent;
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  text-align: left;
  cursor: pointer;
  border-radius: var(--radius-md);
  transition:
    background-color var(--duration-fast) var(--ease-in-out),
    color var(--duration-fast) var(--ease-in-out);
}

.app-sidebar__sublink:hover {
  background-color: var(--color-surface-muted);
  color: var(--color-text);
}

.app-sidebar__sublink.is-active {
  background-color: var(--color-primary-soft);
  color: var(--color-primary);
  font-weight: 600;
}

.app-sidebar__toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 40px;
  margin: var(--space-2);
  border: 1px solid var(--color-border);
  background-color: transparent;
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
  cursor: pointer;
}

.app-sidebar__toggle:hover {
  background-color: var(--color-surface-muted);
  color: var(--color-text);
}

.app-sidebar--collapsed .app-sidebar__group-title {
  justify-content: center;
  padding: var(--space-2);
}

@media (max-width: 767px) {
  .app-sidebar {
    position: fixed;
    inset: 0 auto 0 0;
    z-index: var(--z-fixed);
    width: 280px;
    transform: translateX(-100%);
  }

  .app-sidebar--collapsed {
    transform: translateX(0);
  }
}
</style>
