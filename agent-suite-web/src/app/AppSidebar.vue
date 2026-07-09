<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useRoute } from 'vue-router';

import { router } from '@router/index';
import { dataQueryClient } from '@api/data-query';
import { legalClient } from '@api/legal';
import { recruitmentClient } from '@api/recruitment';
import AppIcon from '@components/ui/AppIcon.vue';
import type { DataThread } from '@/types/data-query';
import type { LegalSession } from '@/types/legal';
import type { RecruitTask } from '@/types/recruitment';

interface SidebarAgent {
  name: string;
  label: string;
  description: string;
  icon: string;
  module: 'legal' | 'recruitment' | 'data';
  accentLabel: string;
}

const props = defineProps<{ collapsed: boolean }>();
const emit = defineEmits<{ (e: 'toggle'): void }>();

const route = useRoute();

const sidebarLabel = '智能体导航';
const workspaceTitle = 'Agent Suite';
const workspaceHint = '法律、招聘与数据助手';
const toggleLabel = computed(() => (props.collapsed ? '展开侧边栏' : '收起侧边栏'));
const activeModule = computed(() => (route.meta?.module ?? null) as SidebarAgent['module'] | null);
const isApiConfigActive = computed(() => route.name === 'admin-api-config');

const agents: SidebarAgent[] = [
  {
    name: 'legal-sessions',
    label: '法律助手',
    description: '合同、纠纷与合规问答',
    icon: 'Document',
    module: 'legal',
    accentLabel: 'Legal',
  },
  {
    name: 'recruit-task-new',
    label: '招聘助手',
    description: '简历分析与匹配建议',
    icon: 'User',
    module: 'recruitment',
    accentLabel: 'Recruit',
  },
  {
    name: 'data-sessions',
    label: '问数助手',
    description: '自然语言查询业务数据',
    icon: 'Histogram',
    module: 'data',
    accentLabel: 'Data',
  },
];

const legalRecentSessions = ref<LegalSession[]>([]);
const recruitRecentTasks = ref<RecruitTask[]>([]);
const dataRecentThreads = ref<DataThread[]>([]);
const recentLoading = ref<Record<SidebarAgent['module'], boolean>>({
  legal: false,
  recruitment: false,
  data: false,
});
const recentError = ref<Record<SidebarAgent['module'], boolean>>({
  legal: false,
  recruitment: false,
  data: false,
});
const activeRecentLoading = computed(() =>
  activeModule.value ? recentLoading.value[activeModule.value] : false,
);
const activeRecentError = computed(() =>
  activeModule.value ? recentError.value[activeModule.value] : false,
);
const activeRecentCount = computed(() => {
  if (activeModule.value === 'legal') return legalRecentSessions.value.length;
  if (activeModule.value === 'recruitment') return recruitRecentTasks.value.length;
  if (activeModule.value === 'data') return dataRecentThreads.value.length;
  return 0;
});

const newConversationRoute = computed(() => {
  if (activeModule.value === 'recruitment') return 'recruit-task-new';
  if (activeModule.value === 'data') return 'data-sessions';
  return 'legal-sessions';
});

function navigate(name: string): void {
  void router.push({ name });
}

async function openLegalSession(session: LegalSession): Promise<void> {
  await router.push({ name: 'legal-session-detail', params: { id: session.public_id } });
}

async function openRecruitTask(task: RecruitTask): Promise<void> {
  await router.push({ name: 'recruit-task-detail', params: { id: task.task_id } });
}

async function openDataThread(thread: DataThread): Promise<void> {
  await router.push({ name: 'data-session-detail', params: { id: thread.thread_id } });
}

function isAgentActive(agent: SidebarAgent): boolean {
  return agent.module === activeModule.value;
}

function formatRecentDate(value: string | null): string {
  if (!value) return '';
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
  }).format(new Date(value));
}

async function loadRecentConversations(): Promise<void> {
  const module = activeModule.value;
  if (props.collapsed || !module) return;

  recentLoading.value[module] = true;
  recentError.value[module] = false;
  try {
    if (module === 'legal') {
      const response = await legalClient.listSessions({ limit: 6, offset: 0 });
      legalRecentSessions.value = response.data.items;
      return;
    }
    if (module === 'recruitment') {
      const response = await recruitmentClient.listTasks({ page: 1, page_size: 6 });
      recruitRecentTasks.value = response.items;
      return;
    }
    const response = await dataQueryClient.listThreads({ limit: 6, offset: 0 });
    dataRecentThreads.value = response.data.items;
  } catch {
    recentError.value[module] = true;
  } finally {
    recentLoading.value[module] = false;
  }
}

watch(
  () => [activeModule.value, props.collapsed, route.fullPath],
  () => {
    if (activeModule.value && !props.collapsed) {
      void loadRecentConversations();
    }
  },
  { immediate: true },
);
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
      <button
        type="button"
        class="app-sidebar__toggle"
        :aria-label="toggleLabel"
        :aria-expanded="!props.collapsed"
        :title="toggleLabel"
        @click="emit('toggle')"
      >
        <AppIcon :name="props.collapsed ? 'Expand' : 'Fold'" />
      </button>
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

      <div v-if="!props.collapsed" class="app-sidebar__recents-shell">
        <section v-if="activeModule" class="app-sidebar__recents" aria-label="最近对话">
          <div class="app-sidebar__recents-header">
            <span>最近对话</span>
            <button
              type="button"
              class="app-sidebar__recents-refresh"
              :disabled="activeRecentLoading"
              aria-label="刷新最近对话"
              @click="loadRecentConversations"
            >
              <AppIcon name="Refresh" />
            </button>
          </div>

          <p v-if="activeRecentLoading" class="app-sidebar__recents-state">加载中…</p>
          <template v-else>
            <template v-if="activeModule === 'legal'">
              <button
                v-for="session in legalRecentSessions"
                :key="session.public_id"
                type="button"
                class="app-sidebar__recent"
                :class="{ 'is-active': route.params.id === session.public_id }"
                @click="openLegalSession(session)"
              >
                <span>{{ session.title || '未命名咨询' }}</span>
                <small>{{ formatRecentDate(session.last_message_at) }}</small>
              </button>
            </template>

            <template v-if="activeModule === 'recruitment'">
              <button
                v-for="task in recruitRecentTasks"
                :key="task.task_id"
                type="button"
                class="app-sidebar__recent"
                :class="{ 'is-active': route.params.id === task.task_id }"
                @click="openRecruitTask(task)"
              >
                <span>{{ task.title || '未命名分析' }}</span>
                <small>{{ formatRecentDate(task.created_at) }}</small>
              </button>
            </template>

            <template v-if="activeModule === 'data'">
              <button
                v-for="thread in dataRecentThreads"
                :key="thread.thread_id"
                type="button"
                class="app-sidebar__recent"
                :class="{ 'is-active': route.params.id === thread.thread_id }"
                @click="openDataThread(thread)"
              >
                <span>{{ thread.title || '未命名对话' }}</span>
                <small>{{ formatRecentDate(thread.updated_at) }}</small>
              </button>
            </template>
          </template>
          <p
            v-if="!activeRecentLoading && !activeRecentError && activeRecentCount === 0"
            class="app-sidebar__recents-state"
          >
            暂无对话
          </p>
          <p v-if="!activeRecentLoading && activeRecentError" class="app-sidebar__recents-state">
            加载失败
          </p>
        </section>
      </div>
    </nav>

    <div class="app-sidebar__footer">
      <button
        type="button"
        class="app-sidebar__utility"
        :class="{ 'is-active': isApiConfigActive }"
        title="API 配置"
        aria-label="API 配置"
        @click="navigate('admin-api-config')"
      >
        <span class="app-sidebar__utility-icon">
          <AppIcon name="Setting" />
        </span>
        <span v-if="!props.collapsed" class="app-sidebar__utility-label">API 配置</span>
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
  flex: 1 1 auto;
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
.app-sidebar__agent-label {
  transition:
    background-color var(--duration-fast) var(--ease-in-out),
    color var(--duration-fast) var(--ease-in-out),
    transform var(--duration-fast) var(--ease-out-expo);
}

.app-sidebar__agent:active {
  transform: scale(0.985);
}

.app-sidebar__recents-shell {
  display: grid;
  gap: var(--space-1);
  margin-top: var(--space-5);
}

.app-sidebar__recents {
  display: grid;
  gap: var(--space-1);
  padding-top: var(--space-3);
  border-top: 1px solid var(--color-border);
}

.app-sidebar__recents-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 28px;
  padding-left: var(--space-3);
  color: var(--color-text-subtle);
  font-size: var(--text-xs);
  font-weight: 700;
}

.app-sidebar__recents-refresh {
  display: inline-grid;
  place-items: center;
  width: 28px;
  height: 28px;
  color: var(--color-text-subtle);
  background: transparent;
  border: 0;
  border-radius: var(--radius-sm);
  cursor: pointer;
}

.app-sidebar__recents-refresh:hover {
  color: var(--color-primary);
  background: var(--color-primary-soft);
}

.app-sidebar__recents-refresh:disabled {
  cursor: progress;
  opacity: 0.6;
}

.app-sidebar__recent {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  min-height: 34px;
  padding: var(--space-2) var(--space-3);
  color: var(--color-text-muted);
  text-align: left;
  background: transparent;
  border: 0;
  cursor: pointer;
}

.app-sidebar__recent:hover,
.app-sidebar__recent.is-active {
  color: var(--color-primary);
  background: var(--color-primary-soft);
}

.app-sidebar__recent span {
  overflow: hidden;
  color: inherit;
  font-size: var(--text-xs);
  font-weight: 650;
  line-height: 1.3;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.app-sidebar__recent small {
  color: var(--color-text-subtle);
  font-size: var(--text-xs);
  line-height: 1.3;
}

.app-sidebar__recents-state {
  margin: 0;
  padding: var(--space-2) var(--space-3);
  color: var(--color-text-subtle);
  font-size: var(--text-xs);
}

.app-sidebar__footer {
  flex: 0 0 auto;
  padding: var(--space-2);
  border-top: 1px solid var(--color-border);
}

.app-sidebar__utility {
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

.app-sidebar__utility:hover,
.app-sidebar__utility.is-active {
  color: var(--color-text);
  background: color-mix(in oklch, var(--color-surface) 72%, var(--color-primary-soft));
}

.app-sidebar__utility-icon {
  display: inline-grid;
  place-items: center;
  width: 28px;
  height: 28px;
  color: inherit;
}

.app-sidebar__utility-label {
  overflow: hidden;
  color: inherit;
  font-size: var(--text-sm);
  font-weight: 650;
  line-height: 1.25;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.app-sidebar__toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
  width: 34px;
  height: 34px;
  color: var(--color-text-muted);
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

.app-sidebar__toggle:hover {
  color: var(--color-text);
  background: var(--color-surface-muted);
}

.app-sidebar--collapsed .app-sidebar__brand {
  flex-direction: column;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-2) var(--space-2);
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
  display: grid;
  place-items: center;
  padding-inline: var(--space-2);
}

.app-sidebar--collapsed .app-sidebar__utility {
  display: flex;
  justify-content: center;
  width: 40px;
  padding: var(--space-2);
}

.app-sidebar--collapsed .app-sidebar__toggle {
  order: -1;
  width: 40px;
  height: 40px;
  padding: 0;
  color: var(--color-text);
  background: var(--color-surface);
}

@media (min-width: 768px) {
  .app-sidebar--collapsed {
    width: 0;
    overflow: hidden;
    border-right: 0;
    pointer-events: none;
  }
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
