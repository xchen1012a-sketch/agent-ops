<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';

import { dataQueryClient } from '@api/data-query';
import AgentChatLanding from '@components/chat/AgentChatLanding.vue';
import { useToastStore } from '@stores/toast';
import { createConversationTitle } from '@lib/conversation-title';

const router = useRouter();
const toast = useToastStore();

const firstQuestion = ref('');
const creating = ref(false);
const suggestions = [
  { label: '门店销售排行', prompt: '本周各门店销售额 Top 10 是哪些？' },
  { label: '客户增长趋势', prompt: '最近 30 天新增客户趋势如何？' },
  { label: '库存周转分析', prompt: '哪些商品库存周转较慢？' },
] as const;

async function createThread(): Promise<void> {
  const question = firstQuestion.value.trim();
  if (!question) return;

  creating.value = true;
  try {
    const response = await dataQueryClient.createThread({
      title: createConversationTitle(question, '问数对话'),
    });
    toast.success('已开始');
    await router.push({
      name: 'data-session-detail',
      params: { id: response.data.thread_id },
      query: { q: question },
    });
  } catch (error) {
    toast.error(error instanceof Error ? error.message : '创建失败，请重试');
  } finally {
    creating.value = false;
  }
}
</script>

<template>
  <AgentChatLanding
    v-model="firstQuestion"
    agent-name="智能问数"
    title="今天想了解哪些数据？"
    description="直接用日常语言提问，我会完成安全查询并整理趋势、排行和结论。"
    icon="DataAnalysis"
    tone="data"
    placeholder="向数据助手提问"
    hint="无需 SQL，Enter 发送"
    :suggestions="suggestions"
    :submitting="creating"
    @submit="createThread"
  />
</template>
