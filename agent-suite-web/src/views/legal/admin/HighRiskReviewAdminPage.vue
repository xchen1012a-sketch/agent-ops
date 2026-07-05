<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue';

import { legalClient } from '@api/legal';
import EmptyState from '@components/ui/EmptyState.vue';
import LoadingState from '@components/ui/LoadingState.vue';
import { useToastStore } from '@stores/toast';
import type { LegalHighRiskReviewAdmin, LegalHighRiskReviewStatus } from '@/types/legal';

const toast = useToastStore();

const reviews = ref<LegalHighRiskReviewAdmin[]>([]);
const loading = ref(false);
const resolving = ref(false);
const statusFilter = ref<LegalHighRiskReviewStatus>('pending');
const resolveDialogVisible = ref(false);
const selectedReview = ref<LegalHighRiskReviewAdmin | null>(null);
const resolveForm = reactive({
  status: 'resolved' as Exclude<LegalHighRiskReviewStatus, 'pending'>,
  resolution: '',
});

async function loadReviews(): Promise<void> {
  loading.value = true;
  try {
    const response = await legalClient.listHighRiskReviews({
      status: statusFilter.value,
      limit: 20,
      offset: 0,
    });
    reviews.value = response.data.items;
  } catch (error) {
    toast.error(error instanceof Error ? error.message : '加载高风险审核队列失败');
  } finally {
    loading.value = false;
  }
}

function openResolveDialog(review: LegalHighRiskReviewAdmin): void {
  selectedReview.value = review;
  resolveForm.status = 'resolved';
  resolveForm.resolution = '';
  resolveDialogVisible.value = true;
}

async function submitResolution(): Promise<void> {
  if (!selectedReview.value?.id || !resolveForm.resolution.trim()) return;
  resolving.value = true;
  try {
    await legalClient.resolveHighRiskReview(selectedReview.value.id, {
      status: resolveForm.status,
      resolution: resolveForm.resolution.trim(),
    });
    toast.success('高风险审核已处理');
    resolveDialogVisible.value = false;
    await loadReviews();
  } catch (error) {
    toast.error(error instanceof Error ? error.message : '处理高风险审核失败');
  } finally {
    resolving.value = false;
  }
}

onMounted(() => {
  void loadReviews();
});
</script>

<template>
  <div class="high-risk-review-page">
    <section class="high-risk-review-page__header" aria-labelledby="high-risk-review-title">
      <div>
        <p class="high-risk-review-page__eyebrow">法律咨询 · 管理员</p>
        <h1 id="high-risk-review-title">高风险审核</h1>
        <p class="high-risk-review-page__description">
          查看用户加入队列的高风险法律咨询回答，并记录复核结果。该页面只调用法律 Agent
          公开审核接口。
        </p>
      </div>
      <el-button :loading="loading" @click="loadReviews">刷新</el-button>
    </section>

    <section class="high-risk-review-page__toolbar" aria-label="审核筛选">
      <el-radio-group v-model="statusFilter" @change="loadReviews">
        <el-radio-button label="pending">待处理</el-radio-button>
        <el-radio-button label="reviewed">已复核</el-radio-button>
        <el-radio-button label="resolved">已解决</el-radio-button>
      </el-radio-group>
    </section>

    <LoadingState v-if="loading" message="正在加载审核队列…" />
    <EmptyState
      v-else-if="reviews.length === 0"
      title="暂无审核记录"
      description="当用户把高风险回答加入复核队列后，会显示在这里。"
      icon="Warning"
    />
    <section v-else class="high-risk-review-page__list" aria-label="高风险审核列表">
      <article v-for="review in reviews" :key="review.id ?? review.message_id" class="review-card">
        <div class="review-card__main">
          <div class="review-card__title">
            <h2>消息 #{{ review.message_id }}</h2>
            <el-tag
              :type="
                review.status === 'pending'
                  ? 'warning'
                  : review.status === 'resolved'
                    ? 'success'
                    : 'info'
              "
              effect="light"
            >
              {{ review.status }}
            </el-tag>
          </div>
          <p class="review-card__reason">{{ review.reason }}</p>
          <p class="review-card__meta">
            用户 #{{ review.user_id }}
            <span v-if="review.reviewed_by"> · 复核人 #{{ review.reviewed_by }}</span>
          </p>
          <p v-if="review.resolution" class="review-card__resolution">
            处理结果：{{ review.resolution }}
          </p>
        </div>
        <el-button
          v-if="review.status === 'pending'"
          type="primary"
          plain
          @click="openResolveDialog(review)"
        >
          处理
        </el-button>
      </article>
    </section>

    <el-dialog v-model="resolveDialogVisible" title="处理高风险审核" width="460px">
      <el-form label-position="top">
        <el-form-item label="处理状态" required>
          <el-radio-group v-model="resolveForm.status">
            <el-radio-button label="reviewed">已复核</el-radio-button>
            <el-radio-button label="resolved">已解决</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="处理说明" required>
          <el-input
            v-model="resolveForm.resolution"
            type="textarea"
            :rows="4"
            maxlength="1000"
            show-word-limit
            placeholder="记录人工复核结论、线下沟通或转办说明。"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resolveDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="resolving"
          :disabled="!resolveForm.resolution.trim()"
          @click="submitResolution"
        >
          保存处理结果
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.high-risk-review-page {
  display: grid;
  gap: var(--space-5);
  max-width: var(--layout-content-max-width);
  margin: 0 auto;
}

.high-risk-review-page__header,
.high-risk-review-page__toolbar,
.review-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
}

.high-risk-review-page__header {
  display: flex;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-6);
}

.high-risk-review-page__eyebrow {
  margin-bottom: var(--space-2);
  color: var(--color-legal);
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.08em;
}

.high-risk-review-page__description,
.review-card__reason,
.review-card__meta,
.review-card__resolution {
  color: var(--color-text-muted);
}

.high-risk-review-page__description {
  max-width: 760px;
  margin-top: var(--space-3);
}

.high-risk-review-page__toolbar {
  padding: var(--space-4);
}

.high-risk-review-page__list {
  display: grid;
  gap: var(--space-3);
}

.review-card {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-4);
}

.review-card__main {
  min-width: 0;
}

.review-card__title {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.review-card__title h2 {
  font-size: var(--text-lg);
}

.review-card__reason,
.review-card__meta,
.review-card__resolution {
  margin-top: var(--space-2);
}

@media (max-width: 767px) {
  .high-risk-review-page__header {
    align-items: flex-start;
    flex-direction: column;
    padding: var(--space-4);
  }

  .review-card {
    display: grid;
  }
}
</style>
