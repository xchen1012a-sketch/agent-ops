<script setup lang="ts">
import { reactive, ref } from 'vue';
import { useRouter } from 'vue-router';

import { recruitmentClient } from '@api/recruitment';
import ChatComposer from '@components/chat/ChatComposer.vue';
import { useToastStore } from '@stores/toast';
import type { RecruitTaskPriority } from '@/types/recruitment';

const router = useRouter();
const toast = useToastStore();

const form = reactive<{
  title: string;
  priority: RecruitTaskPriority;
  resume_text: string;
  jd_text: string;
}>({
  title: '',
  priority: 'normal',
  resume_text: '',
  jd_text: '',
});

const submitting = ref(false);
const draftText = ref('');

const PRIORITY_OPTIONS: { value: RecruitTaskPriority; label: string }[] = [
  { value: 'normal', label: '普通' },
  { value: 'urgent', label: '紧急' },
];

async function submitDraft(): Promise<void> {
  const parsed = parseRecruitDraft(draftText.value);
  if (!parsed) {
    toast.warning('请粘贴简历和岗位说明，并用“岗位说明：”或“JD：”分隔。');
    return;
  }

  form.resume_text = parsed.resume;
  form.jd_text = parsed.jd;
  if (!form.title.trim()) {
    form.title = parsed.jd.split('\n')[0]?.slice(0, 60) || '候选人匹配分析';
  }
  await submit();
}

async function submit(): Promise<void> {
  const resume = form.resume_text.trim();
  const jd = form.jd_text.trim();
  if (!resume || !jd) {
    toast.warning('请同时填写简历文本与岗位说明');
    return;
  }

  submitting.value = true;
  try {
    const response = await recruitmentClient.createTask({
      title: form.title.trim() || null,
      priority: form.priority,
      resume_text: resume,
      jd_text: jd,
    });
    toast.success('任务已创建');
    await router.push({
      name: 'recruit-task-detail',
      params: { id: response.task.task_id },
    });
  } catch (error) {
    toast.error(error instanceof Error ? error.message : '创建失败，请重试');
  } finally {
    submitting.value = false;
  }
}

function cancel(): void {
  void router.push({ name: 'recruit-tasks' });
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
  <div class="recruit-new-task">
    <section class="recruit-new-task__header">
      <div>
        <p class="recruit-new-task__eyebrow">招聘助手</p>
        <h1>新建分析任务</h1>
        <p class="recruit-new-task__desc">
          粘贴脱敏简历与岗位说明，系统会解析要求、匹配证据并生成面试问题。
        </p>
      </div>
    </section>

    <section class="recruit-new-task__quick" aria-label="快速创建招聘分析">
      <ChatComposer
        v-model="draftText"
        tone="recruit"
        placeholder="粘贴脱敏简历，然后另起一行写“岗位说明：”并粘贴 JD"
        hint="Enter 创建任务，Shift + Enter 换行"
        input-label="粘贴简历和岗位说明"
        :max-length="50000"
        :submitting="submitting"
        @submit="submitDraft"
      />
      <p>示例格式：简历：候选人经历… / 岗位说明：岗位职责与要求…。图片简历暂不支持 OCR。</p>
    </section>

    <form class="recruit-new-task__form" @submit.prevent="submit">
      <h2>结构化详情（可选编辑）</h2>
      <div class="recruit-new-task__row">
        <label class="recruit-new-task__field">
          <span>任务标题（可选）</span>
          <el-input v-model="form.title" maxlength="120" placeholder="如：后端工程师候选人评估" />
        </label>
        <label class="recruit-new-task__field recruit-new-task__field--narrow">
          <span>优先级</span>
          <el-select v-model="form.priority" aria-label="优先级">
            <el-option
              v-for="option in PRIORITY_OPTIONS"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </label>
      </div>

      <label class="recruit-new-task__field">
        <span>简历文本</span>
        <el-input
          v-model="form.resume_text"
          type="textarea"
          :rows="8"
          maxlength="50000"
          show-word-limit
          placeholder="粘贴脱敏后的候选人简历文本"
        />
      </label>

      <label class="recruit-new-task__field">
        <span>岗位说明（JD）</span>
        <el-input
          v-model="form.jd_text"
          type="textarea"
          :rows="8"
          maxlength="50000"
          show-word-limit
          placeholder="粘贴岗位职责与要求"
        />
      </label>

      <div class="recruit-new-task__actions">
        <el-button @click="cancel">取消</el-button>
        <el-button type="primary" native-type="submit" :loading="submitting">创建任务</el-button>
      </div>
    </form>
  </div>
</template>

<style scoped>
.recruit-new-task {
  display: grid;
  gap: var(--space-5);
  max-width: 880px;
  margin: 0 auto;
}

.recruit-new-task__header,
.recruit-new-task__quick,
.recruit-new-task__form {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
}

.recruit-new-task__header {
  padding: var(--space-6);
}

.recruit-new-task__quick {
  display: grid;
  gap: var(--space-2);
  padding: var(--space-4);
}

.recruit-new-task__quick p {
  color: var(--color-text-muted);
  font-size: var(--text-xs);
}

.recruit-new-task__eyebrow {
  margin-bottom: var(--space-2);
  color: var(--color-recruit, var(--color-primary));
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.08em;
}

.recruit-new-task__desc {
  margin-top: var(--space-2);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.recruit-new-task__form {
  display: grid;
  gap: var(--space-4);
  padding: var(--space-6);
}

.recruit-new-task__form h2 {
  font-size: var(--text-base);
  font-weight: 700;
}

.recruit-new-task__row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 200px;
  gap: var(--space-4);
}

.recruit-new-task__field {
  display: grid;
  gap: var(--space-2);
}

.recruit-new-task__field > span {
  font-size: var(--text-sm);
  font-weight: 600;
}

.recruit-new-task__actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-2);
}

@media (max-width: 767px) {
  .recruit-new-task__header,
  .recruit-new-task__quick,
  .recruit-new-task__form {
    padding: var(--space-4);
  }

  .recruit-new-task__row {
    grid-template-columns: 1fr;
  }
}
</style>
