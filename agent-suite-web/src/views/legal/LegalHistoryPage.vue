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
const query = ref('');
const loading = ref(false);
const limit = 20;

async function loadRecords(): Promise<void> {
  loading.value = true;
  try {
    const response = await legalClient.listConsultationRecords({
      limit,
      offset: 0,
      q: query.value.trim() || undefined,
    });
    records.value = response.data.items;
  } catch (error) {
    toast.error(error instanceof Error ? error.message : '加载历史咨询失败');
  } finally {
    loading.value = false;
  }
}

async function openReport(recordPublicId: string): Promise<void> {
  await router.push({
    name: 'legal-report-detail',
    params: { id: recordPublicId },
  });
}

onMounted(() => {
  void loadRecords();
});
</script>

<template>
  <div class="legal-history-page">
    <section class="legal-history-page__header" aria-labelledby="legal-history-title">
      <div>
        <p class="legal-history-page__eyebrow">法律咨询</p>
        <h1 id="legal-history-title">历史咨询</h1>
        <p class="legal-history-page__description">
          基于法律 Agent 已公开的 consultation-records 投影查询，不读取完整原始对话。
        </p>
      </div>
    </section>

    <section class="legal-history-page__toolbar" aria-label="历史咨询搜索">
      <el-input
        v-model="query"
        clearable
        placeholder="按摘要关键词搜索，例如：劳动、合同、赔偿"
        aria-label="历史咨询关键词"
        @keyup.enter="loadRecords"
      />
      <el-button type="primary" :loading="loading" @click="loadRecords">搜索</el-button>
    </section>

    <LoadingState v-if="loading" message="正在加载历史咨询…" />
    <EmptyState
      v-else-if="records.length === 0"
      title="暂无历史咨询"
      description="完成一次法律问答后，后端会生成 consultation record，并可在这里检索。"
      icon="Search"
    />
    <section v-else class="legal-history-page__list" aria-label="历史咨询记录">
      <article v-for="record in records" :key="record.public_id" class="legal-record-card">
        <div class="legal-record-card__main">
          <div class="legal-record-card__title">
            <h2>{{ record.summary }}</h2>
            <el-tag v-if="record.high_risk" type="warning" effect="light">高风险</el-tag>
          </div>
          <p class="legal-record-card__disclaimer">{{ record.disclaimer }}</p>
          <p class="legal-record-card__meta">引用数：{{ record.citations?.length ?? 0 }}</p>
        </div>
        <el-button @click="openReport(record.public_id)">查看报告</el-button>
      </article>
    </section>
  </div>
</template>

<style scoped>
.legal-history-page {
  display: grid;
  gap: var(--space-5);
  max-width: var(--layout-content-max-width);
  margin: 0 auto;
}

.legal-history-page__header,
.legal-history-page__toolbar,
.legal-record-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
}

.legal-history-page__header {
  padding: var(--space-6);
}

.legal-history-page__eyebrow {
  margin-bottom: var(--space-2);
  color: var(--color-legal);
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.08em;
}

.legal-history-page__description,
.legal-record-card__disclaimer,
.legal-record-card__meta {
  color: var(--color-text-muted);
}

.legal-history-page__description {
  margin-top: var(--space-3);
}

.legal-history-page__toolbar {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: var(--space-3);
  padding: var(--space-4);
}

.legal-history-page__list {
  display: grid;
  gap: var(--space-3);
}

.legal-record-card {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-4);
}

.legal-record-card__main {
  min-width: 0;
}

.legal-record-card__title {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.legal-record-card__title h2 {
  font-size: var(--text-lg);
}

.legal-record-card__disclaimer {
  margin-top: var(--space-2);
}

.legal-record-card__meta {
  margin-top: var(--space-2);
  font-size: var(--text-sm);
}

@media (max-width: 767px) {
  .legal-history-page__header {
    padding: var(--space-4);
  }

  .legal-history-page__toolbar,
  .legal-record-card {
    grid-template-columns: 1fr;
  }

  .legal-record-card {
    display: grid;
  }
}
</style>
