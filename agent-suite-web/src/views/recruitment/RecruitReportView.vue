<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';

import { recruitmentClient } from '@api/recruitment';
import AsyncState from '@components/ui/AsyncState.vue';
import SafeMarkdown from '@components/ui/SafeMarkdown.vue';
import { createErrorState, createLoadingState, createSuccessState } from '@lib/request-state';
import type { RequestState } from '@/types/request-state';
import type { RecruitReportDetail, RecruitReportFormat } from '@/types/recruitment';

const route = useRoute();

const reportId = computed(() => String(route.params.id));

const state = ref<RequestState<RecruitReportDetail>>({
  status: 'idle',
  data: null,
  error: null,
  updatedAt: null,
});

async function loadReport(): Promise<void> {
  state.value = createLoadingState();
  try {
    const response = await recruitmentClient.getReport(reportId.value);
    state.value = createSuccessState(response.report);
  } catch (error) {
    state.value = createErrorState(error instanceof Error ? error : String(error ?? '加载失败'));
  }
}

function exportUrl(format: RecruitReportFormat): string {
  return recruitmentClient.buildReportExportUrl(reportId.value, format);
}

onMounted(() => {
  void loadReport();
});
</script>

<template>
  <div class="recruit-report">
    <AsyncState :state="state" loading-message="加载报告中…" @retry="loadReport">
      <template #default="{ data }">
        <article v-if="data" class="recruit-report__card">
          <header class="recruit-report__head">
            <div>
              <p class="recruit-report__eyebrow">招聘助手</p>
              <h1>分析报告</h1>
            </div>
            <div class="recruit-report__actions">
              <el-link
                v-for="format in data.format_available"
                :key="format"
                :href="exportUrl(format as RecruitReportFormat)"
                target="_blank"
                rel="noopener"
                type="primary"
              >
                导出 {{ format.toUpperCase() }}
              </el-link>
            </div>
          </header>

          <p class="recruit-report__meta">
            状态：{{ data.status }} · 有效期至 {{ data.expires_at }}
          </p>

          <SafeMarkdown :source="data.content_markdown" />
        </article>
      </template>
    </AsyncState>
  </div>
</template>

<style scoped>
.recruit-report {
  display: grid;
  gap: var(--space-4);
  max-width: 960px;
  margin: 0 auto;
}

.recruit-report__card {
  display: grid;
  gap: var(--space-4);
  padding: var(--space-6);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
}

.recruit-report__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
}

.recruit-report__eyebrow {
  margin-bottom: var(--space-2);
  color: var(--color-recruit, var(--color-primary));
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.08em;
}

.recruit-report__actions {
  display: flex;
  gap: var(--space-3);
}

.recruit-report__meta {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

@media (max-width: 767px) {
  .recruit-report__card {
    padding: var(--space-4);
  }

  .recruit-report__head {
    flex-direction: column;
  }
}
</style>
