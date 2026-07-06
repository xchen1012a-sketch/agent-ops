<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';

import { router } from '@router/index';
import AppIcon from '@components/ui/AppIcon.vue';

interface SidebarAction {
  name: string;
  label: string;
  icon: string;
}

interface SidebarAgent {
  name: string;
  label: string;
  description: string;
  icon: string;
  module: 'legal' | 'recruitment' | 'data';
  accentLabel: string;
  actions: SidebarAction[];
}

const props = defineProps<{ collapsed: boolean }>();
const emit = defineEmits<{ (e: 'toggle'): void }>();

const route = useRoute();

const sidebarLabel = '智能体导航';
const workspaceTitle = 'Agent Suite';
const workspaceHint = '法律、招聘与数据助手';
const toggleLabel = computed(() => (props.collapsed ? '展开侧边栏' : '收起侧边栏'));
const activeModule = computed(() => (route.meta?.module ?? null) as SidebarAgent['module'] | null);

const agents: SidebarAgent[] = [
  {
    name: 'legal-sessions',
    label: '法律助手',
    description: '合同、纠纷与合规问答',
    icon: 'Document',
    module: 'legal',
    accentLabel: 'Legal',
    actions: [
      { name: 'legal-sessions', label: '新咨询', icon: 'Plus' },
      { name: 'legal-history', label: '咨询记录', icon: 'Search' },
      { name: 'legal-reports', label: '法律报告', icon: 'Notebook' },
    ],
  },
  {
    name: 'recruit-tasks',
    label: '招聘助手',
    description: '简历分析与匹配建议',
    icon: 'User',
    module: 'recruitment',
    accentLabel: 'Recruit',
    actions: [
      { name: 'recruit-task-new', label: '新分析', icon: 'Plus' },
      { name: 'recruit-tasks', label: '招聘任务', icon: 'List' },
      { name: 'recruit-reports', label: '匹配报告', icon: 'DataAnalysis' },
    ],
  },
  {
    name: 'data-sessions',
    label: '问数助手',
    description: '自然语言查询业务数据',
    icon: 'Histogram',
    module: 'data',
    accentLabel: 'Data',
    actions: [
      { name: 'data-sessions', label: '新问数', icon: 'Plus' },
      { name: 'data-history', label: '查询历史', icon: 'Search' },
    ],
  },
];

const activeAgent = computed(
  () => agents.find((agent) => agent.module === activeModule.value) ?? agents[0],
);

const newConversationRoute = computed(() => {
  if (activeModule.value === 'recruitment') return 'recruit-task-new';
  if (activeModule.value === 'data') return 'data-sessions';
  return 'legal-sessions';
});

function navigate(name: string): void {
  void router.push({ name });
}

function isAgentActive(agent: SidebarAgent): boolean {
  return agent.module === activeModule.value;
}

function isActionActive(action: SidebarAction): boolean {
  return (
    route.name === action.name || Boolean(route.name?.toString().startsWith(`${action.name}-`))
  );
}
</script>

<template>
  <aside
    class="app-sidebar"
    :class="{ 'app-sidebar--collapsed': props.collapsed }"
    :aria-label="sidebarLabel"
  >
    <div class="app-sidebar__brand">
      <button
        type="button"
        class="app-sidebar__mark"
        aria-label="回到法律助手"
        @click="navigate('legal-sessions')"
      >
        <span aria-hidden="true">A</span>
      </button>
      <div v-if="!props.collapsed" class="app-sidebar__brand-copy">
        <strong>{{ workspaceTitle }}</strong>
        <span>{{ workspaceHint }}</span>
      </div>
    </div>

    <button
      type="button"
      class="app-sidebar__new"
      :title="props.collapsed ? '新对话' : undefined"
      @click="navigate(newConversationRoute)"
    >
      <AppIcon name="Plus" />
      <span v-if="!props.collapsed">新对话</span>
    </button>

    <nav class="app-sidebar__nav" role="navigation">
      <p v-if="!props.collapsed" class="app-sidebar__section-label">Agents</p>
      <button
        v-for="agent in agents"
        :key="agent.name"
        type="button"
        class="app-sidebar__agent"
        :class="[`app-sidebar__agent--${agent.module}`, { 'is-active': isAgentActive(agent) }]"
        :title="agent.label"
        @click="navigate(agent.name)"
      >
        <span class="app-sidebar__agent-icon">
          <AppIcon :name="agent.icon" />
        </span>
        <span v-if="!props.collapsed" class="app-sidebar__agent-label">{{ agent.label }}</span>
      </button>

      <div v-if="!props.collapsed" class="app-sidebar__actions">
        <p class="app-sidebar__section-label">{{ activeAgent.label }}</p>
        <button
          v-for="action in activeAgent.actions"
          :key="action.name"
          type="button"
          class="app-sidebar__action"
          :class="{ 'is-active': isActionActive(action) }"
          @click="navigate(action.name)"
        >
          <AppIcon :name="action.icon" />
          <span>{{ action.label }}</span>
        </button>
      </div>
    </nav>

    <div class="app-sidebar__footer">
      <button
        type="button"
        class="app-sidebar__utility"
        :class="{ 'is-active': route.name === 'admin-api-config' }"
        :title="props.collapsed ? 'API 配置' : undefined"
        @click="navigate('admin-api-config')"
      >
        <AppIcon name="Setting" />
        <span v-if="!props.collapsed">API 配置</span>
      </button>
      <button
        type="button"
        class="app-sidebar__toggle"
        :aria-label="toggleLabel"
        :aria-expanded="!props.collapsed"
        @click="emit('toggle')"
      >
        <AppIcon :name="props.collapsed ? 'Expand' : 'Fold'" />
      </button>
    </div>
  </aside>
</template>

<style scoped>
.app-sidebar {
  position: sticky;
  top: 0;
  display: flex;
  flex-direction: column;
  height: 100vh;
  min-width: 0;
  background: color-mix(in oklch, var(--color-bg) 82%, var(--color-surface));
  border-right: 1px solid var(--color-border);
  transition:
    width var(--duration-normal) var(--ease-in-out),
    transform var(--duration-normal) var(--ease-in-out);
}

.app-sidebar__brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  min-height: var(--layout-header-height);
  padding: var(--space-3);
}

.app-sidebar__mark,
.app-sidebar__new,
.app-sidebar__agent,
.app-sidebar__action,
.app-sidebar__utility,
.app-sidebar__toggle {
  border: 0;
  font: inherit;
  cursor: pointer;
}

.app-sidebar__mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
  width: 36px;
  height: 36px;
  color: var(--color-primary);
  background: var(--color-primary-soft);
  border: 1px solid color-mix(in oklch, var(--color-primary) 30%, var(--color-border));
  border-radius: var(--radius-lg);
}

.app-sidebar__mark span {
  font-size: var(--text-sm);
  font-weight: 750;
}

.app-sidebar__brand-copy,
.app-sidebar__agent-copy {
  display: grid;
  min-width: 0;
}

.app-sidebar__brand-copy strong {
  color: var(--color-text);
  font-size: var(--text-sm);
  line-height: 1.25;
}

.app-sidebar__brand-copy span,
.app-sidebar__agent-description {
  overflow: hidden;
  color: var(--color-text-subtle);
  font-size: var(--text-xs);
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.app-sidebar__new {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  min-height: 42px;
  margin: 0 var(--space-3) var(--space-4);
  color: var(--color-text);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-pill);
  box-shadow: var(--shadow-card);
  transition:
    background-color var(--duration-fast) var(--ease-in-out),
    border-color var(--duration-fast) var(--ease-in-out),
    color var(--duration-fast) var(--ease-in-out);
}

.app-sidebar__new:hover {
  color: var(--color-primary);
  border-color: color-mix(in oklch, var(--color-primary) 36%, var(--color-border));
}

.app-sidebar__nav {
  flex: 1 1 auto;
  padding: 0 var(--space-2) var(--space-3);
  overflow-y: auto;
}

.app-sidebar__section-label {
  margin: 0 0 var(--space-2);
  padding-inline: var(--space-3);
  color: var(--color-text-subtle);
  font-size: var(--text-xs);
  font-weight: 700;
}

.app-sidebar__agent {
  display: grid;
  grid-template-columns: 28px minmax(0, 1fr);
  align-items: center;
  gap: var(--space-3);
  width: 100%;
  min-height: 40px;
  padding: var(--space-2);
  color: var(--color-text-muted);
  text-align: left;
  background: transparent;
  border-radius: var(--radius-lg);
  transition:
    background-color var(--duration-fast) var(--ease-in-out),
    color var(--duration-fast) var(--ease-in-out);
}

.app-sidebar__agent:hover,
.app-sidebar__agent.is-active {
  color: var(--color-text);
  background: color-mix(in oklch, var(--color-surface) 72%, var(--color-primary-soft));
}

.app-sidebar__agent-icon {
  display: inline-grid;
  place-items: center;
  width: 28px;
  height: 28px;
  color: var(--color-text-muted);
  background: var(--color-surface-muted);
  border-radius: var(--radius-sm);
}

.app-sidebar__agent.is-active .app-sidebar__agent-icon {
  color: var(--color-primary);
  background: var(--color-primary-soft);
}

.app-sidebar__agent-label {
  overflow: hidden;
  color: inherit;
  font-size: var(--text-sm);
  font-weight: 650;
  line-height: 1.25;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.app-sidebar__agent-icon,
.app-sidebar__agent-label,
.app-sidebar__action,
.app-sidebar__utility {
  transition:
    background-color var(--duration-fast) var(--ease-in-out),
    color var(--duration-fast) var(--ease-in-out),
    transform var(--duration-fast) var(--ease-out-expo);
}

.app-sidebar__agent:active,
.app-sidebar__action:active,
.app-sidebar__utility:active {
  transform: scale(0.985);
}

.app-sidebar__actions {
  display: grid;
  gap: var(--space-1);
  margin-top: var(--space-5);
}

.app-sidebar__action,
.app-sidebar__utility {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  width: 100%;
  min-height: 36px;
  padding: var(--space-2) var(--space-3);
  color: var(--color-text-muted);
  text-align: left;
  background: transparent;
  border-radius: var(--radius-md);
}

.app-sidebar__action:hover,
.app-sidebar__action.is-active,
.app-sidebar__utility:hover,
.app-sidebar__utility.is-active {
  color: var(--color-primary);
  background: var(--color-primary-soft);
}

.app-sidebar__footer {
  display: grid;
  gap: var(--space-2);
  padding: var(--space-3);
}

.app-sidebar__toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 40px;
  color: var(--color-text-muted);
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-pill);
}

.app-sidebar__toggle:hover {
  color: var(--color-text);
  background: var(--color-surface-muted);
}

.app-sidebar--collapsed .app-sidebar__brand {
  justify-content: center;
  padding-inline: var(--space-2);
}

.app-sidebar--collapsed .app-sidebar__new {
  width: 40px;
  margin-inline: auto;
}

.app-sidebar--collapsed .app-sidebar__nav {
  padding-inline: var(--space-2);
}

.app-sidebar--collapsed .app-sidebar__agent {
  display: flex;
  justify-content: center;
  padding: var(--space-2);
}

.app-sidebar--collapsed .app-sidebar__footer {
  align-items: center;
}

.app-sidebar--collapsed .app-sidebar__utility,
.app-sidebar--collapsed .app-sidebar__toggle {
  justify-content: center;
  width: 40px;
  min-height: 40px;
  padding: 0;
}

@media (max-width: 767px) {
  .app-sidebar {
    position: fixed;
    inset: 0 auto 0 0;
    z-index: var(--z-fixed);
    width: 292px;
    transform: translateX(-100%);
    box-shadow: var(--shadow-floating);
  }

  .app-sidebar--collapsed {
    transform: translateX(0);
  }
}
</style>
