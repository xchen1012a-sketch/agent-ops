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
    toast.error(error instanceof Error ? error.message : '加载失败');
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
        <p class="legal-history-page__eyebrow">法律助手</p>
        <h1 id="legal-history-title">咨询记录</h1>
      </div>
    </section>

    <section class="legal-history-page__toolbar" aria-label="搜索记录">
      <el-input
        v-model="query"
        clearable
        placeholder="搜索关键词"
        aria-label="搜索记录"
        @keyup.enter="loadRecords"
      />
      <el-button type="primary" :loading="loading" @click="loadRecords">搜索</el-button>
    </section>

    <LoadingState v-if="loading" message="加载中…" />
    <EmptyState
      v-else-if="records.length === 0"
      title="暂无记录"
      description="开始一次咨询后，这里会自动保存。"
      icon="Search"
    />
    <section v-else class="legal-history-page__list" aria-label="咨询记录">
      <article v-for="record in records" :key="record.public_id" class="legal-record-card">
        <div class="legal-record-card__main">
          <div class="legal-record-card__title">
            <h2>{{ record.summary }}</h2>
            <el-tag v-if="record.high_risk" type="warning" effect="light">需确认</el-tag>
          </div>
          <p class="legal-record-card__meta">{{ record.citations?.length ?? 0 }} 条依据</p>
        </div>
        <el-button @click="openReport(record.public_id)">查看</el-button>
      </article>
    </section>
  </div>
</template>

<style scoped>
.legal-history-page {
  display: grid;
  gap: var(--space-5);
  max-width: 960px;
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

.legal-record-card__meta {
  margin-top: var(--space-2);
  color: var(--color-text-muted);
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
