<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';

import { legalClient } from '@api/legal';
import EmptyState from '@components/ui/EmptyState.vue';
import LoadingState from '@components/ui/LoadingState.vue';
import { useToastStore } from '@stores/toast';
import type { LegalConsultationRecord } from '@/types/legal';

const router = useRouter();
const toast = useToastStore();

const records = ref<LegalConsultationRecord[]>([]);
const loading = ref(false);

async function loadReports(): Promise<void> {
  loading.value = true;
  try {
    const response = await legalClient.listConsultationRecords({ limit: 50, offset: 0 });
    records.value = response.data.items;
  } catch (error) {
    toast.error(error instanceof Error ? error.message : '加载失败');
  } finally {
    loading.value = false;
  }
}

async function openReport(recordPublicId: string): Promise<void> {
  await router.push({ name: 'legal-report-detail', params: { id: recordPublicId } });
}

onMounted(() => {
  void loadReports();
});
</script>

<template>
  <div class="legal-report-list">
    <section class="legal-report-list__header" aria-labelledby="legal-report-list-title">
      <div>
        <p class="legal-report-list__eyebrow">法律助手</p>
        <h1 id="legal-report-list-title">我的报告</h1>
      </div>
      <el-button :loading="loading" @click="loadReports">刷新</el-button>
    </section>

    <LoadingState v-if="loading" message="加载中…" />
    <EmptyState
      v-else-if="records.length === 0"
      title="暂无报告"
      description="完成咨询后，可在这里查看整理结果。"
      icon="Notebook"
    />
    <section v-else class="legal-report-list__grid" aria-label="报告列表">
      <article v-for="record in records" :key="record.public_id" class="report-card">
        <div class="report-card__title">
          <h2>{{ record.summary }}</h2>
          <el-tag v-if="record.high_risk" type="warning" effect="light">需确认</el-tag>
        </div>
        <p class="report-card__meta">{{ record.citations?.length ?? 0 }} 条依据</p>
        <el-button type="primary" plain @click="openReport(record.public_id)">查看</el-button>
      </article>
    </section>
  </div>
</template>

<style scoped>
.legal-report-list {
  display: grid;
  gap: var(--space-5);
  max-width: 960px;
  margin: 0 auto;
}

.legal-report-list__header,
.report-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
}

.legal-report-list__header {
  display: flex;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-6);
}

.legal-report-list__eyebrow {
  margin-bottom: var(--space-2);
  color: var(--color-legal);
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.08em;
}

.legal-report-list__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-4);
}

.report-card {
  display: grid;
  gap: var(--space-3);
  padding: var(--space-4);
}

.report-card__title {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3);
}

.report-card__title h2 {
  font-size: var(--text-lg);
}

.report-card__meta {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

@media (max-width: 767px) {
  .legal-report-list__header {
    align-items: flex-start;
    flex-direction: column;
    padding: var(--space-4);
  }

  .legal-report-list__grid {
    grid-template-columns: 1fr;
  }
}
</style>
