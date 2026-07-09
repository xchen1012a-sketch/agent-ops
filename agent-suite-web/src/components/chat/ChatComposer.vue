<script setup lang="ts">
import { ref } from 'vue';

import AppIcon from '@components/ui/AppIcon.vue';

type ComposerTone = 'legal' | 'recruit' | 'data';
type NoticeTone = 'info' | 'warning';

interface AttachmentPreview {
  name: string;
  size: string;
  state: 'read' | 'pending';
}

const props = withDefaults(
  defineProps<{
    modelValue: string;
    tone: ComposerTone;
    placeholder: string;
    hint: string;
    inputLabel: string;
    submitting?: boolean;
    disabled?: boolean;
    disabledReason?: string;
    maxLength?: number;
    showModelSelector?: boolean;
  }>(),
  {
    submitting: false,
    disabled: false,
    disabledReason: '',
    maxLength: 2000,
    showModelSelector: false,
  },
);

const emit = defineEmits<{
  (event: 'update:modelValue', value: string): void;
  (event: 'submit'): void;
}>();

const fileInput = ref<HTMLInputElement | null>(null);
const attachments = ref<AttachmentPreview[]>([]);
const notice = ref<{ tone: NoticeTone; message: string } | null>(null);
const selectedModel = ref('Sonnet 5 High');

const modelOptions = ['Sonnet 5 High', 'Sonnet 5', 'Haiku 4.5'] as const;

const TEXT_FILE_EXTENSIONS = new Set([
  '.csv',
  '.json',
  '.log',
  '.md',
  '.sql',
  '.txt',
  '.yaml',
  '.yml',
]);
const TEXT_FILE_READ_LIMIT = 80_000;

function submit(): void {
  if (props.disabled || props.submitting || !props.modelValue.trim()) return;
  emit('submit');
}

function handleKeydown(event: KeyboardEvent): void {
  if (event.key !== 'Enter' || event.shiftKey || event.isComposing) return;
  event.preventDefault();
  submit();
}

async function handlePaste(event: ClipboardEvent): Promise<void> {
  const files = filesFromClipboard(event);
  if (files.length === 0) return;

  event.preventDefault();
  await handleFiles(files);
}

async function handleFileSelection(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement;
  await handleFiles(Array.from(input.files ?? []));
  input.value = '';
}

async function handleFiles(files: File[]): Promise<void> {
  const imageFiles = files.filter(isImageFile);
  const usableFiles = files.filter((file) => !isImageFile(file));

  if (imageFiles.length > 0) {
    notice.value = {
      tone: 'warning',
      message: '当前 MVP 还没有接入 OCR，图片暂时不能识别。请粘贴文字，或使用文本类文件。',
    };
  }

  if (usableFiles.length === 0) return;

  const readableFiles = usableFiles.filter(isReadableTextFile);
  const pendingFiles = usableFiles.filter((file) => !isReadableTextFile(file));

  for (const file of readableFiles) {
    await appendTextFile(file);
  }

  if (pendingFiles.length > 0) {
    attachments.value.push(
      ...pendingFiles.map((file) => ({
        name: file.name,
        size: formatFileSize(file.size),
        state: 'pending' as const,
      })),
    );
    notice.value = {
      tone: 'info',
      message: '已识别文件，但当前后端还没有文件解析链路；发送给模型的仍是输入框里的文字。',
    };
  } else if (readableFiles.length > 0 && imageFiles.length === 0) {
    notice.value = {
      tone: 'info',
      message: '已把文本文件内容追加到输入框。',
    };
  }
}

async function appendTextFile(file: File): Promise<void> {
  if (file.size > TEXT_FILE_READ_LIMIT) {
    attachments.value.push({
      name: file.name,
      size: formatFileSize(file.size),
      state: 'pending',
    });
    notice.value = {
      tone: 'info',
      message: '文件较大，当前不会自动读入；请复制关键内容到输入框后再发送。',
    };
    return;
  }

  const text = await file.text();
  const content = [`[文件：${file.name}]`, text.trim()].filter(Boolean).join('\n');
  attachments.value.push({
    name: file.name,
    size: formatFileSize(file.size),
    state: 'read',
  });
  appendToInput(content);
}

function appendToInput(content: string): void {
  const current = props.modelValue.trimEnd();
  emit('update:modelValue', current ? `${current}\n\n${content}` : content);
}

function filesFromClipboard(event: ClipboardEvent): File[] {
  const items = Array.from(event.clipboardData?.items ?? []);
  return items
    .filter((item) => item.kind === 'file')
    .map((item) => item.getAsFile())
    .filter((file): file is File => Boolean(file));
}

function isImageFile(file: File): boolean {
  return file.type.startsWith('image/') || imageExtension(file.name);
}

function imageExtension(name: string): boolean {
  return /\.(avif|bmp|gif|heic|jpeg|jpg|png|svg|webp)$/i.test(name);
}

function isReadableTextFile(file: File): boolean {
  if (file.type.startsWith('text/')) return true;
  const lowerName = file.name.toLowerCase();
  return Array.from(TEXT_FILE_EXTENSIONS).some((extension) => lowerName.endsWith(extension));
}

function formatFileSize(size: number): string {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / 1024 / 1024).toFixed(1)} MB`;
}

function selectModel(model: string): void {
  selectedModel.value = model;
}
</script>

<template>
  <form class="chat-composer" :class="`chat-composer--${props.tone}`" @submit.prevent="submit">
    <div class="chat-composer__input" @keydown="handleKeydown" @paste="handlePaste">
      <el-input
        :model-value="props.modelValue"
        type="textarea"
        :autosize="{ minRows: 1, maxRows: 5 }"
        :maxlength="props.maxLength"
        resize="none"
        :disabled="props.disabled"
        :placeholder="props.placeholder"
        :aria-label="props.inputLabel"
        @update:model-value="emit('update:modelValue', $event)"
      />
    </div>

    <div v-if="attachments.length" class="chat-composer__attachments" aria-label="已粘贴文件">
      <span
        v-for="attachment in attachments"
        :key="`${attachment.name}-${attachment.size}`"
        class="chat-composer__attachment"
        :class="`chat-composer__attachment--${attachment.state}`"
      >
        <AppIcon name="Files" />
        <span>{{ attachment.name }}</span>
        <small>{{ attachment.state === 'read' ? '已读入' : attachment.size }}</small>
      </span>
    </div>

    <div
      v-if="notice"
      class="chat-composer__notice"
      :class="`chat-composer__notice--${notice.tone}`"
      role="status"
    >
      {{ notice.message }}
    </div>

    <div class="chat-composer__toolbar">
      <div class="chat-composer__left">
        <!-- eslint-disable-next-line vue/html-self-closing -->
        <input
          ref="fileInput"
          class="chat-composer__file-input"
          type="file"
          multiple
          accept=".txt,.md,.csv,.json,.sql,.log,.yaml,.yml,.pdf,.doc,.docx"
          @change="handleFileSelection"
        />
        <el-button
          class="chat-composer__attach"
          text
          circle
          type="info"
          :disabled="props.disabled || props.submitting"
          aria-label="粘贴或选择文件"
          @click="fileInput?.click()"
        >
          <AppIcon name="Plus" />
        </el-button>
        <span v-if="props.disabled && props.disabledReason" class="chat-composer__hint">
          {{ props.disabledReason }}
        </span>
      </div>

      <div class="chat-composer__right">
        <el-dropdown v-if="props.showModelSelector" trigger="click" @command="selectModel">
          <button type="button" class="chat-composer__model" aria-label="选择模型">
            <span>{{ selectedModel }}</span>
            <AppIcon name="ArrowDown" />
          </button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item
                v-for="model in modelOptions"
                :key="model"
                :command="model"
                :disabled="model === selectedModel"
              >
                {{ model }}
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <el-button
          class="chat-composer__send"
          type="primary"
          circle
          native-type="submit"
          :loading="props.submitting"
          :disabled="props.disabled || !props.modelValue.trim()"
          aria-label="发送"
        >
          <AppIcon name="Expand" />
        </el-button>
      </div>
    </div>
  </form>
</template>

<style scoped>
.chat-composer {
  --chat-tone: var(--color-primary);
  --chat-tone-soft: var(--color-primary-soft);

  display: grid;
  gap: var(--space-2);
  padding: var(--space-4);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
  transition:
    border-color var(--duration-fast) var(--ease-in-out),
    box-shadow var(--duration-fast) var(--ease-in-out);
}

.chat-composer--legal {
  --chat-tone: var(--color-legal);
  --chat-tone-soft: var(--color-legal-soft);
}

.chat-composer--recruit {
  --chat-tone: var(--color-recruit);
  --chat-tone-soft: var(--color-recruit-soft);
}

.chat-composer--data {
  --chat-tone: var(--color-data);
  --chat-tone-soft: var(--color-data-soft);
}

.chat-composer:focus-within {
  border-color: color-mix(in oklch, var(--chat-tone) 42%, var(--color-border));
  box-shadow:
    var(--shadow-card),
    0 0 0 3px color-mix(in oklch, var(--chat-tone) 10%, transparent);
}

.chat-composer__input :deep(.el-textarea__inner) {
  min-height: 46px !important;
  padding: var(--space-2) var(--space-1);
  background: transparent;
  border: 0;
  box-shadow: none;
  line-height: var(--line-relaxed);
}

.chat-composer__attachments {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.chat-composer__attachment {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  max-width: min(100%, 280px);
  min-height: 32px;
  padding: 0 var(--space-2);
  color: var(--color-text-muted);
  background: var(--color-surface-muted);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-pill);
  font-size: var(--text-xs);
}

.chat-composer__attachment--read {
  color: var(--chat-tone);
  background: var(--chat-tone-soft);
  border-color: color-mix(in oklch, var(--chat-tone) 28%, var(--color-border));
}

.chat-composer__attachment span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-composer__attachment small {
  flex: 0 0 auto;
  color: var(--color-text-subtle);
}

.chat-composer__notice {
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md);
  font-size: var(--text-xs);
  line-height: var(--line-normal);
}

.chat-composer__notice--info {
  color: var(--color-text-muted);
  background: var(--color-surface-muted);
}

.chat-composer__notice--warning {
  color: var(--color-warning);
  background: var(--color-warning-soft);
}

.chat-composer__toolbar,
.chat-composer__left,
.chat-composer__right {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.chat-composer__toolbar {
  justify-content: space-between;
  min-height: 40px;
  color: var(--color-text-subtle);
  font-size: var(--text-xs);
}

.chat-composer__left {
  min-width: 0;
}

.chat-composer__hint {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-composer__file-input {
  display: none;
}

.chat-composer__attach,
.chat-composer__send {
  flex: 0 0 auto;
  width: 36px;
  height: 36px;
  font-size: var(--text-base);
}

.chat-composer__attach {
  color: var(--color-text);
}

.chat-composer__model {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  min-height: 36px;
  padding: 0 var(--space-2);
  border: 0;
  background: transparent;
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.chat-composer__model:hover {
  color: var(--color-text);
}

.chat-composer__model .app-icon {
  width: 0.9em;
  height: 0.9em;
  color: var(--color-text-subtle);
}

@media (max-width: 767px) {
  .chat-composer__hint {
    max-width: 48vw;
  }

  .chat-composer__model span {
    max-width: 112px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}
</style>
