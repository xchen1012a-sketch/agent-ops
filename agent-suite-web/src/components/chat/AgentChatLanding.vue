<script setup lang="ts">
import AppIcon from '@components/ui/AppIcon.vue';
import ChatComposer from '@components/chat/ChatComposer.vue';

interface Suggestion {
  label: string;
  prompt: string;
}

const props = withDefaults(
  defineProps<{
    modelValue: string;
    agentName: string;
    title: string;
    description: string;
    icon: string;
    tone: 'legal' | 'recruit' | 'data';
    placeholder: string;
    hint: string;
    suggestions: readonly Suggestion[];
    submitting?: boolean;
    disabled?: boolean;
    disabledReason?: string;
  }>(),
  {
    submitting: false,
    disabled: false,
    disabledReason: '',
  },
);

const emit = defineEmits<{
  (event: 'update:modelValue', value: string): void;
  (event: 'submit'): void;
}>();

function chooseSuggestion(prompt: string): void {
  if (props.disabled) return;
  emit('update:modelValue', prompt);
}
</script>

<template>
  <div class="agent-chat-landing" :class="`agent-chat-landing--${props.tone}`">
    <section class="agent-chat-landing__welcome" :aria-labelledby="`${props.tone}-chat-title`">
      <span class="agent-chat-landing__avatar" aria-hidden="true">
        <AppIcon :name="props.icon" />
      </span>
      <p>{{ props.agentName }}</p>
      <h1 :id="`${props.tone}-chat-title`">{{ props.title }}</h1>
      <span class="agent-chat-landing__description">{{ props.description }}</span>
    </section>

    <section class="agent-chat-landing__interaction" :aria-label="`${props.agentName}输入区`">
      <ChatComposer
        :model-value="props.modelValue"
        :tone="props.tone"
        :placeholder="props.placeholder"
        :hint="props.hint"
        :input-label="`向${props.agentName}提问`"
        :submitting="props.submitting"
        :disabled="props.disabled"
        :disabled-reason="props.disabledReason"
        @update:model-value="emit('update:modelValue', $event)"
        @submit="emit('submit')"
      />

      <div class="agent-chat-landing__suggestions" aria-label="快捷问题">
        <el-button
          v-for="suggestion in props.suggestions"
          :key="suggestion.label"
          round
          plain
          :disabled="props.disabled"
          @click="chooseSuggestion(suggestion.prompt)"
        >
          {{ suggestion.label }}
        </el-button>
      </div>
    </section>

    <slot name="after" />
  </div>
</template>

<style scoped>
.agent-chat-landing {
  --chat-tone: var(--color-primary);
  --chat-tone-soft: var(--color-primary-soft);

  display: grid;
  align-content: center;
  gap: var(--space-6);
  width: min(100%, 820px);
  min-height: calc(100vh - 240px);
  margin: 0 auto;
  padding: var(--space-8) 0;
}

.agent-chat-landing--legal {
  --chat-tone: var(--color-legal);
  --chat-tone-soft: var(--color-legal-soft);
}

.agent-chat-landing--recruit {
  --chat-tone: var(--color-recruit);
  --chat-tone-soft: var(--color-recruit-soft);
}

.agent-chat-landing--data {
  --chat-tone: var(--color-data);
  --chat-tone-soft: var(--color-data-soft);
}

.agent-chat-landing__welcome {
  display: grid;
  justify-items: center;
  gap: var(--space-2);
  text-align: center;
}

.agent-chat-landing__avatar {
  display: grid;
  place-items: center;
  width: 48px;
  height: 48px;
  margin-bottom: var(--space-2);
  color: var(--chat-tone);
  background: var(--chat-tone-soft);
  border: 1px solid color-mix(in oklch, var(--chat-tone) 28%, var(--color-border));
  border-radius: var(--radius-md);
  font-size: var(--text-xl);
}

.agent-chat-landing__welcome p {
  color: var(--chat-tone);
  font-size: var(--text-xs);
  font-weight: 760;
  letter-spacing: 0.08em;
}

.agent-chat-landing__welcome h1 {
  font-size: 2.6rem;
  font-weight: 720;
  letter-spacing: 0;
}

.agent-chat-landing__description {
  max-width: 560px;
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  line-height: var(--line-relaxed);
}

.agent-chat-landing__interaction {
  display: grid;
  gap: var(--space-3);
}

.agent-chat-landing__suggestions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--space-2);
}

.agent-chat-landing__suggestions .el-button {
  min-height: 40px;
  margin: 0;
  color: var(--color-text-muted);
  background: var(--color-surface);
  border-color: var(--color-border);
  box-shadow: var(--shadow-card);
}

.agent-chat-landing__suggestions .el-button:hover {
  color: var(--chat-tone);
  border-color: var(--chat-tone);
}

@media (max-width: 767px) {
  .agent-chat-landing {
    align-content: start;
    gap: var(--space-5);
    min-height: calc(100vh - 180px);
    padding: var(--space-8) 0 var(--space-6);
  }

  .agent-chat-landing__welcome h1 {
    font-size: 2rem;
  }

  .agent-chat-landing__description {
    font-size: var(--text-xs);
  }
}
</style>
