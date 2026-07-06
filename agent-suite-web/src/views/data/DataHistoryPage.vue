<script setup lang="ts">
import { onMounted, ref } from 'vue';

import { dataQueryClient } from '@api/data-query';
import AsyncState from '@components/ui/AsyncState.vue';
import { useToastStore } from '@stores/toast';
import {
  createErrorState,
  createLoadingState,
  createSuccessState,
  toRequestError,
} from '@lib/request-state';
import type { DataQueryHistoryItem, DataQueryHistoryListData } from '@/types/data-query';
import type { RequestState } from '@/types/request-state';

const toast = useToastStore();
const limit = 20;
const state = ref<RequestState<DataQueryHistoryListData>>({
  status: 'idle',
  data: null,
  error: null,
  updatedAt: null,
});
const detailVisible = ref(false);
const detailLoading = ref(false);
const selectedDetail = ref<DataQueryHistoryItem | null>(null);

async function loadHistory(): Promise<void> {
  state.value = createLoadingState();
  try {
    const response = await dataQueryClient.listQueryHistory({ limit, offset: 0 });
    state.value = createSuccessState(response.data, {
      isEmpty: (data) => data.items.length === 0,
    });
  } catch (error) {
    state.value = createErrorState(toRequestError(error));
  }
}

async function openDetail(queryId: string): Promise<void> {
  detailVisible.value = true;
  detailLoading.value = true;
  selectedDetail.value = null;
  try {
    const response = await dataQueryClient.getQueryHistory(queryId);
    selectedDetail.value = response.data;
  } catch (error) {
    toast.error(error instanceof Error ? error.message : '加载查询历史详情失败');
    detailVisible.value = false;
  } finally {
    detailLoading.value = false;
  }
}

function statusType(status: string): 'success' | 'warning' | 'danger' | 'info' | 'primary' {
  switch (status) {
    case 'success':
      return 'success';
    case 'failed':
      return 'danger';
    case 'canceled':
      return 'warning';
    case 'running':
    case 'retrying':
      return 'primary';
    default:
      return 'info';
  }
}

function formatDate(value: string | null): string {
  if (!value) return '—';
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value));
}

onMounted(() => {
  void loadHistory();
});
</script>

<template>
  <div class="data-history-page">
    <section class="data-history-page__header" aria-labelledby="data-history-title">
      <div>
        <p class="data-history-page__eyebrow">智能问数</p>
        <h1 id="data-history-title">查询历史</h1>
        <p class="data-history-page__description">
          展示当前用户自己的 query-history 投影。该普通用户接口不会暴露 SQL、策略细节或结果行数据。
        </p>
      </div>
      <el-button :loading="state.status === 'loading'" @click="loadHistory">刷新</el-button>
    </section>

    <AsyncState
      :state="state"
      loading-message="正在加载查询历史…"
      empty-title="暂无查询历史"
      empty-description="提交问数问题后，运行摘要会显示在这里。"
      @retry="loadHistory"
    >
      <template #default="{ data }">
        <section class="data-history-page__list" aria-label="智能问数查询历史列表">
          <article v-for="item in data?.items ?? []" :key="item.query_id" class="data-history-card">
            <div class="data-history-card__main">
              <div class="data-history-card__title">
                <h2>{{ item.query_id }}</h2>
                <el-tag :type="statusType(item.status)" effect="light">{{ item.status }}</el-tag>
              </div>
              <p>创建：{{ formatDate(item.created_at) }}</p>
              <p>
                开始：{{ formatDate(item.started_at) }} · 结束：{{ formatDate(item.finished_at) }}
              </p>
              <p v-if="item.error_code" class="data-history-card__error">
                错误码：{{ item.error_code }}
              </p>
            </div>
            <el-button @click="openDetail(item.query_id)">查看详情</el-button>
          </article>
        </section>
      </template>
    </AsyncState>

    <el-dialog v-model="detailVisible" title="查询历史详情" width="560px">
      <div v-if="detailLoading" class="data-history-page__dialog-loading">加载中…</div>
      <dl v-else-if="selectedDetail" class="data-history-page__detail">
        <dt>Query ID</dt>
        <dd>{{ selectedDetail.query_id }}</dd>
        <dt>状态</dt>
        <dd>{{ selectedDetail.status }}</dd>
        <dt>错误码</dt>
        <dd>{{ selectedDetail.error_code || '—' }}</dd>
        <dt>创建时间</dt>
        <dd>{{ formatDate(selectedDetail.created_at) }}</dd>
        <dt>开始时间</dt>
        <dd>{{ formatDate(selectedDetail.started_at) }}</dd>
        <dt>结束时间</dt>
        <dd>{{ formatDate(selectedDetail.finished_at) }}</dd>
      </dl>
    </el-dialog>
  </div>
</template>

<style scoped>
.data-history-page {
  display: grid;
  gap: var(--space-5);
  max-width: var(--layout-content-max-width);
  margin: 0 auto;
}

.data-history-page__header,
.data-history-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
}

.data-history-page__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-6);
}

.data-history-page__eyebrow {
  margin-bottom: var(--space-2);
  color: var(--color-data);
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.08em;
}

.data-history-page__description,
.data-history-card p {
  color: var(--color-text-muted);
}

.data-history-page__description {
  margin-top: var(--space-3);
}

.data-history-page__list {
  display: grid;
  gap: var(--space-3);
}

.data-history-card {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-4);
}

.data-history-card__main {
  display: grid;
  gap: var(--space-2);
  min-width: 0;
}

.data-history-card__title {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.data-history-card__title h2,
.data-history-card p,
.data-history-page__detail dd {
  overflow-wrap: anywhere;
}

.data-history-card__title h2 {
  font-size: var(--text-lg);
}

.data-history-card__error {
  color: var(--color-danger);
}

.data-history-page__dialog-loading {
  padding: var(--space-4);
  color: var(--color-text-muted);
}

.data-history-page__detail {
  display: grid;
  grid-template-columns: 110px minmax(0, 1fr);
  gap: var(--space-3);
}

.data-history-page__detail dt {
  color: var(--color-text-muted);
}

.data-history-page__detail dd {
  margin: 0;
}

@media (max-width: 767px) {
  .data-history-page__header,
  .data-history-card {
    display: grid;
  }
}
</style>
