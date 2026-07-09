<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';

import { recruitmentClient } from '@api/recruitment';
import AsyncState from '@components/ui/AsyncState.vue';
import {
  createErrorState,
  createLoadingState,
  createSuccessState,
  toRequestError,
} from '@lib/request-state';
import type { RequestState } from '@/types/request-state';
import type {
  RecruitTask,
  RecruitTaskListResponse,
  RecruitReviewStatus,
  RecruitTaskStatus,
} from '@/types/recruitment';

const router = useRouter();

const pageSize = 20;
const page = ref(1);
const state = ref<RequestState<RecruitTaskListResponse>>({
  status: 'idle',
  data: null,
  error: null,
  updatedAt: null,
});

const total = computed(() => state.value.data?.total ?? 0);

const STATUS_LABEL: Record<RecruitTaskStatus, string> = {
  uploaded: '已上传',
  parsing: '解析中',
  parsed: '已解析',
  matching: '匹配中',
  reviewing: '复核中',
  completed: '已完成',
  failed: '失败',
};

const REVIEW_LABEL: Record<RecruitReviewStatus, string> = {
  pending: '待复核',
  approved: '已通过',
  rejected: '已驳回',
  changes_requested: '待修改',
};

function statusTagType(status: RecruitTaskStatus): 'success' | 'danger' | 'info' | 'warning' {
  if (status === 'completed') return 'success';
  if (status === 'failed') return 'danger';
  if (status === 'reviewing') return 'warning';
  return 'info';
}

async function loadTasks(): Promise<void> {
  state.value = createLoadingState();
  try {
    const response = await recruitmentClient.listTasks({
      page: page.value,
      page_size: pageSize,
    });
    state.value = createSuccessState(response, {
      isEmpty: (data) => data.items.length === 0,
    });
  } catch (error) {
    state.value = createErrorState(toRequestError(error));
  }
}

function goNewTask(): void {
  void router.push({ name: 'recruit-task-new' });
}

function openTask(task: RecruitTask): void {
  void router.push({ name: 'recruit-task-detail', params: { id: task.task_id } });
}

async function changePage(next: number): Promise<void> {
  page.value = next;
  await loadTasks();
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value));
}

onMounted(() => {
  void loadTasks();
});
</script>

<template>
  <div class="recruit-task-list">
    <section class="recruit-task-list__header">
      <div>
        <p class="recruit-task-list__eyebrow">招聘助手</p>
        <h1>招聘任务</h1>
      </div>
      <div class="recruit-task-list__actions">
        <el-button :loading="state.status === 'loading'" @click="loadTasks">刷新</el-button>
        <el-button type="primary" @click="goNewTask">新建分析</el-button>
      </div>
    </section>

    <AsyncState
      :state="state"
      loading-message="加载任务中…"
      empty-title="暂无招聘任务"
      empty-description="点击「新建分析」上传简历与岗位说明，开始一次候选人匹配分析。"
      empty-action-text="新建分析"
      @retry="loadTasks"
      @empty-action="goNewTask"
    >
      <template #default="{ data }">
        <section class="recruit-task-list__grid" aria-label="招聘任务列表">
          <article
            v-for="task in data?.items ?? []"
            :key="task.task_id"
            class="recruit-task-card"
            tabindex="0"
            role="button"
            @click="openTask(task)"
            @keyup.enter="openTask(task)"
          >
            <div class="recruit-task-card__title">
              <h2>{{ task.title || '未命名任务' }}</h2>
              <el-tag size="small" :type="statusTagType(task.status)" effect="light">
                {{ STATUS_LABEL[task.status] }}
              </el-tag>
            </div>
            <div class="recruit-task-card__meta">
              <span>
                材料：{{ task.material_summary.has_resume ? '简历' : '缺简历' }} /
                {{ task.material_summary.has_jd ? 'JD' : '缺 JD' }}
              </span>
              <el-tag size="small" effect="plain">{{ REVIEW_LABEL[task.review_status] }}</el-tag>
            </div>
            <p class="recruit-task-card__date">{{ formatDate(task.created_at) }}</p>
          </article>
        </section>

        <div v-if="total > pageSize" class="recruit-task-list__pager">
          <el-pagination
            layout="prev, pager, next"
            :current-page="page"
            :page-size="pageSize"
            :total="total"
            @current-change="changePage"
          />
        </div>
      </template>
    </AsyncState>
  </div>
</template>

<style scoped>
.recruit-task-list {
  display: grid;
  gap: var(--space-5);
  max-width: 1040px;
  margin: 0 auto;
}

.recruit-task-list__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-6);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
}

.recruit-task-list__eyebrow {
  margin-bottom: var(--space-2);
  color: var(--color-recruit, var(--color-primary));
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.08em;
}

.recruit-task-list__actions {
  display: flex;
  gap: var(--space-2);
}

.recruit-task-list__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--space-3);
}

.recruit-task-card {
  display: grid;
  gap: var(--space-3);
  padding: var(--space-4);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  cursor: pointer;
  transition: border-color var(--duration-fast, 150ms) ease;
}

.recruit-task-card:hover,
.recruit-task-card:focus-visible {
  border-color: var(--color-recruit, var(--color-primary));
  outline: none;
}

.recruit-task-card__title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}

.recruit-task-card__title h2 {
  min-width: 0;
  overflow: hidden;
  font-size: var(--text-lg);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.recruit-task-card__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.recruit-task-card__date {
  color: var(--color-text-subtle);
  font-size: var(--text-xs);
}

.recruit-task-list__pager {
  display: flex;
  justify-content: center;
}

@media (max-width: 767px) {
  .recruit-task-list__header {
    flex-direction: column;
    padding: var(--space-4);
  }

  .recruit-task-list__grid {
    grid-template-columns: 1fr;
  }
}
</style>
