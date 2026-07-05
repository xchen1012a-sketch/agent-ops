<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';

import { legalClient } from '@api/legal';
import EmptyState from '@components/ui/EmptyState.vue';
import LoadingState from '@components/ui/LoadingState.vue';
import SafeMarkdown from '@components/ui/SafeMarkdown.vue';
import { useToastStore } from '@stores/toast';
import type { LegalReport } from '@/types/legal';

const route = useRoute();
const toast = useToastStore();

const report = ref<LegalReport | null>(null);
const loading = ref(false);

async function loadReport(): Promise<void> {
  loading.value = true;
  try {
    const response = await legalClient.getConsultationReport(String(route.params.id));
    report.value = response.data;
  } catch (error) {
    toast.error(error instanceof Error ? error.message : '加载咨询报告失败');
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  void loadReport();
});
</script>

<template>
  <div class="legal-report-view">
    <section class="legal-report-view__header" aria-labelledby="legal-report-title">
      <div>
        <p class="legal-report-view__eyebrow">咨询报告</p>
        <h1 id="legal-report-title">法律咨询报告</h1>
        <p class="legal-report-view__description">
          当前展示后端同步生成的 Markdown 报告投影；PDF 导出等待后端公开契约后接入。
        </p>
      </div>
      <el-button :loading="loading" @click="loadReport">刷新报告</el-button>
    </section>

    <LoadingState v-if="loading" message="正在加载咨询报告…" />
    <EmptyState
      v-else-if="!report"
      title="报告不可用"
      description="请从历史咨询记录进入报告详情。"
      icon="DocumentRemove"
    />
    <article v-else class="legal-report-view__content">
      <div class="legal-report-view__meta">
        <el-tag type="info" effect="light">{{ report.format }}</el-tag>
        <span>记录 ID：{{ report.record_public_id }}</span>
      </div>
      <SafeMarkdown :source="report.content" variant="citation" />
    </article>
  </div>
</template>

<style scoped>
.legal-report-view {
  display: grid;
  gap: var(--space-5);
  max-width: var(--layout-content-max-width);
  margin: 0 auto;
}

.legal-report-view__header,
.legal-report-view__content {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
}

.legal-report-view__header {
  display: flex;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-6);
}

.legal-report-view__eyebrow {
  margin-bottom: var(--space-2);
  color: var(--color-legal);
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.08em;
}

.legal-report-view__description,
.legal-report-view__meta {
  color: var(--color-text-muted);
}

.legal-report-view__description {
  margin-top: var(--space-3);
}

.legal-report-view__content {
  padding: var(--space-6);
}

.legal-report-view__meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
  font-size: var(--text-sm);
}

@media (max-width: 767px) {
  .legal-report-view__header {
    align-items: flex-start;
    flex-direction: column;
    padding: var(--space-4);
  }

  .legal-report-view__content {
    padding: var(--space-4);
  }
}
</style>
