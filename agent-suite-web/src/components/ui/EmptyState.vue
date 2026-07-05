<script setup lang="ts">
import AppIcon from '@components/ui/AppIcon.vue';

interface Props {
  title: string;
  description?: string;
  icon?: string;
  actionText?: string;
}

const props = withDefaults(defineProps<Props>(), {
  icon: 'Box',
  description: '',
  actionText: '',
});

const emit = defineEmits<{ (e: 'action'): void }>();
</script>

<template>
  <div class="empty-state" role="status">
    <el-icon class="empty-state__icon" :size="40">
      <AppIcon :name="props.icon" />
    </el-icon>
    <h3 class="empty-state__title">
      {{ title }}
    </h3>
    <p v-if="description" class="empty-state__description">
      {{ description }}
    </p>
    <el-button v-if="actionText" type="primary" @click="emit('action')">
      {{ actionText }}
    </el-button>
  </div>
</template>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-12) var(--space-6);
  text-align: center;
  color: var(--color-text-muted);
}

.empty-state__icon {
  color: var(--color-text-muted);
}

.empty-state__title {
  margin: var(--space-2) 0 0;
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--color-text);
}

.empty-state__description {
  max-width: 480px;
  margin: 0;
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}
</style>
