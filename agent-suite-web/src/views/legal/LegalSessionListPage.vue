<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';

import { legalClient } from '@api/legal';
import AgentChatLanding from '@components/chat/AgentChatLanding.vue';
import { useToastStore } from '@stores/toast';
import { createConversationTitle } from '@lib/conversation-title';

const router = useRouter();
const toast = useToastStore();

const firstQuestion = ref('');
const submitting = ref(false);
const suggestions = [
  { label: '拖欠工资怎么办', prompt: '公司拖欠工资，我该怎么处理？' },
  { label: '押金不退怎么办', prompt: '租房押金不退，可以怎么维权？' },
  { label: '审查合同条款', prompt: '合同里这条违约责任是否合理？' },
] as const;

async function createSession(): Promise<void> {
  const question = firstQuestion.value.trim();
  if (!question) return;

  submitting.value = true;
  try {
    const response = await legalClient.createSession({
      category_code: 'labor',
      title: createConversationTitle(question, '法律咨询'),
    });
    toast.success('已开始');
    await router.push({
      name: 'legal-session-detail',
      params: { id: response.data.public_id },
      query: { q: question },
    });
  } catch (error) {
    toast.error(error instanceof Error ? error.message : '创建失败，请重试');
  } finally {
    submitting.value = false;
  }
}
</script>

<template>
  <AgentChatLanding
    v-model="firstQuestion"
    agent-name="法律助手"
    title="今天想咨询什么法律问题？"
    description="描述事实和诉求，我会先拆解风险，再提供有依据的处理建议。"
    icon="ChatDotRound"
    tone="legal"
    placeholder="向法律助手提问"
    hint="Enter 发送，Shift + Enter 换行"
    :suggestions="suggestions"
    :submitting="submitting"
    @submit="createSession"
  />
</template>
