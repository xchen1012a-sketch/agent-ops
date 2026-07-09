<script setup lang="ts">
import { computed } from 'vue';

import { renderMarkdown } from '@lib/markdown';

interface Props {
  source: string | null | undefined;
  variant?: 'default' | 'citation';
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'default',
});

const html = computed(() => renderMarkdown(props.source));
</script>

<template>
  <!-- eslint-disable vue/no-v-html --内容由 renderMarkdown 经 DOMPurify 净化，参见 @lib/markdown -->
  <div class="safe-markdown" :class="`safe-markdown--${variant}`" v-html="html" />
</template>

<style scoped>
.safe-markdown {
  font-size: var(--text-base);
  line-height: var(--line-relaxed);
  color: var(--color-text);
  word-break: break-word;
}

.safe-markdown :deep(h1),
.safe-markdown :deep(h2),
.safe-markdown :deep(h3),
.safe-markdown :deep(h4),
.safe-markdown :deep(h5),
.safe-markdown :deep(h6) {
  margin: var(--space-4) 0 var(--space-2);
  font-weight: 600;
  line-height: var(--line-tight);
}

.safe-markdown :deep(h1) {
  font-size: var(--text-2xl);
}

.safe-markdown :deep(h2) {
  font-size: var(--text-xl);
}

.safe-markdown :deep(h3) {
  font-size: var(--text-lg);
}

.safe-markdown :deep(p) {
  margin: 0 0 var(--space-3);
}

.safe-markdown :deep(ul),
.safe-markdown :deep(ol) {
  margin: 0 0 var(--space-3);
  padding-left: var(--space-6);
}

.safe-markdown :deep(li) {
  margin: var(--space-1) 0;
}

.safe-markdown :deep(a) {
  color: var(--color-primary);
  text-decoration: underline;
}

.safe-markdown :deep(blockquote) {
  margin: var(--space-3) 0;
  padding: var(--space-2) var(--space-4);
  border-left: 4px solid var(--color-primary);
  background-color: var(--color-primary-soft);
  color: var(--color-text);
  border-radius: 0 var(--radius-md) var(--radius-md) 0;
}

.safe-markdown--citation :deep(blockquote) {
  border-left-color: var(--color-legal);
  background-color: var(--color-legal-soft);
}

.safe-markdown :deep(code) {
  padding: 2px 6px;
  background-color: var(--color-surface-muted);
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
  font-size: 0.9em;
}

.safe-markdown :deep(pre) {
  margin: var(--space-3) 0;
  padding: var(--space-3);
  background-color: var(--color-surface-muted);
  border-radius: var(--radius-md);
  overflow-x: auto;
}

.safe-markdown :deep(pre code) {
  padding: 0;
  background-color: transparent;
}

.safe-markdown :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: var(--space-3) 0;
}

.safe-markdown :deep(th),
.safe-markdown :deep(td) {
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--color-border);
  text-align: left;
}

.safe-markdown :deep(th) {
  background-color: var(--color-surface-muted);
  font-weight: 600;
}
</style>
