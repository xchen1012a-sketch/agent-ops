<script setup lang="ts">
import { reactive, ref } from 'vue';
import { useRouter } from 'vue-router';

import { legalClient } from '@api/legal';
import EmptyState from '@components/ui/EmptyState.vue';
import { useToastStore } from '@stores/toast';

const router = useRouter();
const toast = useToastStore();

const form = reactive({
  category_code: 'labor',
  title: '',
});
const submitting = ref(false);

async function createSession(): Promise<void> {
  submitting.value = true;
  try {
    const response = await legalClient.createSession({
      category_code: form.category_code,
      title: form.title.trim() || null,
    });
    toast.success('法律咨询会话已创建');
    await router.push({
      name: 'legal-session-detail',
      params: { id: response.data.public_id },
    });
  } catch (error) {
    toast.error(error instanceof Error ? error.message : '创建会话失败，请稍后重试');
  } finally {
    submitting.value = false;
  }
}
</script>

<template>
  <div class="legal-session-list">
    <section class="legal-session-list__hero" aria-labelledby="legal-session-list-title">
      <div>
        <p class="legal-session-list__eyebrow">法律咨询</p>
        <h1 id="legal-session-list-title">新建法律咨询</h1>
        <p class="legal-session-list__description">
          当前前端优先接入法律 Agent 已公开的会话创建与问答 API。会话列表接口尚未公开，
          因此本页先提供新建入口，历史咨询请从“历史搜索”查看。
        </p>
      </div>
    </section>

    <section class="legal-session-list__content" aria-label="创建法律咨询会话">
      <el-card shadow="never" class="legal-session-list__card">
        <template #header>
          <div class="legal-session-list__card-header">
            <span>创建会话</span>
            <el-tag type="info" effect="light">公开契约：POST /sessions</el-tag>
          </div>
        </template>

        <el-form label-position="top" @submit.prevent="createSession">
          <el-form-item label="法律分类代码" required>
            <el-input
              v-model="form.category_code"
              autocomplete="off"
              aria-label="法律分类代码"
              placeholder="例如 labor / contract / marriage"
            />
            <p class="legal-session-list__help">
              后端当前要求小写字母开头，可包含数字和下划线；正式分类管理后会改为选择器。
            </p>
          </el-form-item>
          <el-form-item label="会话标题">
            <el-input
              v-model="form.title"
              maxlength="120"
              show-word-limit
              autocomplete="off"
              aria-label="会话标题"
              placeholder="例如：劳动合同解除咨询"
            />
          </el-form-item>
          <el-button
            type="primary"
            native-type="submit"
            :loading="submitting"
            :disabled="!form.category_code.trim()"
          >
            创建并开始咨询
          </el-button>
        </el-form>
      </el-card>

      <EmptyState
        class="legal-session-list__notice"
        title="会话列表等待后端契约"
        description="法律 Agent 当前公开实现包含创建会话、消息列表和问答接口，尚未公开 GET /sessions。前端不猜测未公开字段。"
        icon="ChatLineRound"
      />
    </section>
  </div>
</template>

<style scoped>
.legal-session-list {
  display: grid;
  gap: var(--space-6);
  max-width: var(--layout-content-max-width);
  margin: 0 auto;
}

.legal-session-list__hero,
.legal-session-list__card {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

.legal-session-list__hero {
  padding: var(--space-6);
  background: var(--color-surface);
  box-shadow: var(--shadow-card);
}

.legal-session-list__eyebrow {
  margin-bottom: var(--space-2);
  color: var(--color-legal);
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.08em;
}

.legal-session-list__description,
.legal-session-list__help {
  color: var(--color-text-muted);
}

.legal-session-list__description {
  max-width: 760px;
  margin-top: var(--space-3);
}

.legal-session-list__content {
  display: grid;
  grid-template-columns: minmax(0, 480px) minmax(0, 1fr);
  gap: var(--space-4);
  align-items: stretch;
}

.legal-session-list__card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}

.legal-session-list__help {
  margin-top: var(--space-2);
  font-size: var(--text-xs);
}

.legal-session-list__notice {
  min-height: 100%;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

@media (max-width: 1023px) {
  .legal-session-list__content {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 767px) {
  .legal-session-list__hero {
    padding: var(--space-4);
  }

  .legal-session-list__card-header {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
