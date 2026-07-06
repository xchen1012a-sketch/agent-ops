<script setup lang="ts">
import { computed, ref } from 'vue';
import { useRouter } from 'vue-router';

import { recruitmentClient } from '@api/recruitment';
import AgentChatLanding from '@components/chat/AgentChatLanding.vue';
import { useToastStore } from '@stores/toast';
import type { RecruitTaskPriority } from '@/types/recruitment';

const router = useRouter();
const toast = useToastStore();

const draftText = ref('');
const submitting = ref(false);
const assistantStatus = ref('把脱敏简历和岗位说明发给我，我会创建匹配分析任务。');

const parsedDraft = computed(() => parseRecruitDraft(draftText.value));
const draftSummary = computed(() => {
  if (!draftText.value.trim()) return '';
  if (!parsedDraft.value)
    return `已收到 ${draftText.value.trim().length} 字内容，等待岗位说明分隔。`;
  return `已识别简历 ${parsedDraft.value.resume.length} 字，岗位说明 ${parsedDraft.value.jd.length} 字。`;
});

const suggestions = [
  {
    label: '候选人匹配分析',
    prompt:
      '简历：\n候选人经历、项目、技能、教育背景...\n\n岗位说明：\n岗位职责、任职要求、加分项...',
  },
  {
    label: '紧急岗位评估',
    prompt:
      '紧急\n\n简历：\n候选人经历、项目、技能、教育背景...\n\nJD：\n岗位职责、任职要求、加分项...',
  },
  {
    label: '生成面试关注点',
    prompt:
      '简历：\n候选人经历、项目、技能、教育背景...\n\n职位要求：\n岗位职责、任职要求、加分项...',
  },
] as const;

async function submitDraft(): Promise<void> {
  const parsed = parseRecruitDraft(draftText.value);
  if (!parsed) {
    assistantStatus.value = '我还没有同时识别到简历和岗位说明，请用“岗位说明：”或“JD：”分隔。';
    toast.warning('请粘贴简历和岗位说明，并用“岗位说明：”或“JD：”分隔。');
    return;
  }

  submitting.value = true;
  assistantStatus.value = '我已读到简历和岗位说明，正在创建招聘分析任务。';
  try {
    const response = await recruitmentClient.createTask({
      title: createTaskTitle(parsed.jd),
      priority: inferPriority(draftText.value),
      resume_text: parsed.resume,
      jd_text: parsed.jd,
    });
    toast.success('任务已创建');
    await router.push({
      name: 'recruit-task-detail',
      params: { id: response.task.task_id },
    });
  } catch (error) {
    assistantStatus.value = '任务创建失败，请稍后重试。';
    toast.error(error instanceof Error ? error.message : '创建失败，请重试');
  } finally {
    submitting.value = false;
  }
}

function createTaskTitle(jd: string): string {
  const firstLine = jd
    .split('\n')
    .map((line) => line.trim())
    .find(Boolean);
  return firstLine?.slice(0, 60) || '候选人匹配分析';
}

function inferPriority(value: string): RecruitTaskPriority {
  return /紧急|urgent|高优先级/i.test(value) ? 'urgent' : 'normal';
}

function parseRecruitDraft(value: string): { resume: string; jd: string } | null {
  const normalized = value.trim();
  if (!normalized) return null;

  const marker = normalized.match(/\n\s*(岗位说明|岗位要求|职位要求|JD|Job Description)\s*[:：]/i);
  if (!marker || marker.index === undefined) return null;

  const resume = stripSectionLabel(
    normalized.slice(0, marker.index),
    /^(简历|候选人|Resume)\s*[:：]/i,
  );
  const jd = stripSectionLabel(
    normalized.slice(marker.index),
    /^(岗位说明|岗位要求|职位要求|JD|Job Description)\s*[:：]/i,
  );
  if (!resume || !jd) return null;
  return { resume, jd };
}

function stripSectionLabel(value: string, pattern: RegExp): string {
  return value.trim().replace(pattern, '').trim();
}
</script>

<template>
  <AgentChatLanding
    v-model="draftText"
    agent-name="招聘助手"
    title="今天要分析哪位候选人？"
    description="把简历和岗位说明放进对话里，我会创建匹配分析并进入任务对话。"
    icon="User"
    tone="recruit"
    placeholder="粘贴脱敏简历，然后另起一行写“岗位说明：”并粘贴 JD"
    hint="Enter 创建分析，Shift + Enter 换行"
    :suggestions="suggestions"
    :submitting="submitting"
    @submit="submitDraft"
  >
    <template #after>
      <section class="recruit-new-task__thread" aria-label="招聘助手对话状态">
        <article
          v-if="draftSummary"
          class="recruit-new-task__message recruit-new-task__message--user"
        >
          <span class="recruit-new-task__avatar">我</span>
          <div class="recruit-new-task__bubble">
            {{ draftSummary }}
          </div>
        </article>

        <article class="recruit-new-task__message recruit-new-task__message--assistant">
          <span class="recruit-new-task__avatar">招</span>
          <div class="recruit-new-task__bubble">
            {{ assistantStatus }}
          </div>
        </article>
      </section>
    </template>
  </AgentChatLanding>
</template>

<style scoped>
.recruit-new-task__thread {
  display: grid;
  gap: var(--space-5);
  width: min(100%, 720px);
  margin: var(--space-3) auto 0;
}

.recruit-new-task__message {
  display: grid;
  grid-template-columns: 32px minmax(0, 1fr);
  align-items: flex-start;
  gap: var(--space-3);
}

.recruit-new-task__message--user {
  grid-template-columns: minmax(0, 1fr);
  max-width: min(72%, 620px);
  margin-left: auto;
}

.recruit-new-task__message--user .recruit-new-task__avatar {
  display: none;
}

.recruit-new-task__avatar {
  display: grid;
  flex: 0 0 auto;
  place-items: center;
  width: 32px;
  height: 32px;
  color: var(--color-text-muted);
  background: var(--color-surface-muted);
  border-radius: 50%;
  font-size: var(--text-xs);
  font-weight: 700;
}

.recruit-new-task__message--assistant .recruit-new-task__avatar {
  align-self: end;
  color: var(--color-recruit);
  background: transparent;
  font-size: 0;
}

.recruit-new-task__message--assistant .recruit-new-task__avatar::before {
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  color: var(--color-recruit);
  background: var(--color-recruit-soft);
  border-radius: var(--radius-pill);
  font-size: var(--text-xs);
  font-weight: 750;
  content: 'AI';
}

.recruit-new-task__bubble {
  max-width: min(100%, 620px);
  padding: 0 0 var(--space-1);
  color: var(--color-text-muted);
  background: transparent;
  border: 0;
  border-radius: 0;
  box-shadow: none;
  font-size: var(--text-sm);
  line-height: var(--line-relaxed);
}

.recruit-new-task__message--user .recruit-new-task__bubble {
  justify-self: end;
  color: var(--color-text);
  background: var(--color-surface-muted);
  padding: var(--space-3) var(--space-4);
  border-radius: 14px;
}

@media (max-width: 767px) {
  .recruit-new-task__thread {
    width: 100%;
  }
}
</style>
