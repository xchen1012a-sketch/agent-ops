<script setup lang="ts">
import AppIcon from '@components/ui/AppIcon.vue';

interface Props {
  title: string;
  description: string;
  availableEndpoints?: string[];
  pendingEndpoints?: string[];
}

const contractPendingLabel = '\u5951\u7ea6\u7b49\u5f85\u72b6\u6001';
const availableEndpointsLabel = '\u5f53\u524d\u53ef\u7528\u516c\u5f00\u63a5\u53e3';
const pendingEndpointsLabel = '\u7b49\u5f85\u540e\u7aef\u516c\u5f00\u5951\u7ea6';

const props = withDefaults(defineProps<Props>(), {
  availableEndpoints: () => [],
  pendingEndpoints: () => [],
});
</script>

<template>
  <section class="contract-pending" :aria-label="contractPendingLabel">
    <div class="contract-pending__icon" aria-hidden="true">
      <el-icon :size="32"><AppIcon name="DocumentChecked" /></el-icon>
    </div>
    <div class="contract-pending__content">
      <p class="contract-pending__eyebrow">{{ contractPendingLabel }}</p>
      <h1>{{ props.title }}</h1>
      <p class="contract-pending__description">{{ props.description }}</p>

      <div class="contract-pending__columns">
        <div v-if="props.availableEndpoints.length" class="contract-pending__card">
          <h2>{{ availableEndpointsLabel }}</h2>
          <ul>
            <li v-for="endpoint in props.availableEndpoints" :key="endpoint">
              <code>{{ endpoint }}</code>
            </li>
          </ul>
        </div>
        <div v-if="props.pendingEndpoints.length" class="contract-pending__card">
          <h2>{{ pendingEndpointsLabel }}</h2>
          <ul>
            <li v-for="endpoint in props.pendingEndpoints" :key="endpoint">
              <code>{{ endpoint }}</code>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.contract-pending {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: var(--space-4);
  max-width: var(--layout-content-max-width);
  margin: 0 auto;
  padding: var(--space-6);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
}

.contract-pending__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  color: var(--color-legal);
  background: var(--color-legal-soft);
  border-radius: var(--radius-lg);
}

.contract-pending__content {
  min-width: 0;
}

.contract-pending__eyebrow {
  margin-bottom: var(--space-2);
  color: var(--color-legal);
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.08em;
}

.contract-pending__description {
  max-width: 780px;
  margin-top: var(--space-3);
  color: var(--color-text-muted);
}

.contract-pending__columns {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-4);
  margin-top: var(--space-5);
}

.contract-pending__card {
  min-width: 0;
  padding: var(--space-4);
  background: var(--color-surface-muted);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}

.contract-pending__card h2 {
  margin-bottom: var(--space-3);
  font-size: var(--text-base);
}

.contract-pending__card ul {
  display: grid;
  gap: var(--space-2);
  padding-left: var(--space-5);
}

.contract-pending__card code {
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  overflow-wrap: anywhere;
}

@media (max-width: 767px) {
  .contract-pending {
    grid-template-columns: 1fr;
    padding: var(--space-4);
  }

  .contract-pending__columns {
    grid-template-columns: 1fr;
  }
}
</style>
