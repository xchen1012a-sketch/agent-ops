<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';

import { router } from '@router/index';

const route = useRoute();
const homeLabel = '\u5de5\u4f5c\u53f0';
const breadcrumbLabel = '\u5f53\u524d\u4f4d\u7f6e';

interface Crumb {
  title: string;
  to?: string;
}

const moduleLabels: Record<string, Crumb> = {
  legal: { title: '\u6cd5\u5f8b\u54a8\u8be2', to: '/legal' },
  recruitment: { title: '\u667a\u80fd\u62db\u8058', to: '/recruitment' },
  data: { title: '\u667a\u80fd\u95ee\u6570', to: '/data' },
};

const crumbs = computed<Crumb[]>(() => {
  const title = route.meta?.title;
  const module = route.meta?.module;
  const list: Crumb[] = [];

  if (typeof module === 'string' && moduleLabels[module]) {
    list.push(moduleLabels[module]);
  }
  if (title) {
    list.push({ title: String(title) });
  }
  return list;
});

function navigate(to: string | undefined): void {
  if (!to) return;
  void router.push(to);
}
</script>

<template>
  <nav v-if="crumbs.length" class="app-breadcrumb" :aria-label="breadcrumbLabel">
    <ol class="app-breadcrumb__list">
      <li>
        <RouterLink to="/" class="app-breadcrumb__home">{{ homeLabel }}</RouterLink>
      </li>
      <li v-for="(crumb, index) in crumbs" :key="index" class="app-breadcrumb__item">
        <span class="app-breadcrumb__separator" aria-hidden="true">/</span>
        <button
          v-if="crumb.to && index < crumbs.length - 1"
          type="button"
          class="app-breadcrumb__link"
          @click="navigate(crumb.to)"
        >
          {{ crumb.title }}
        </button>
        <span v-else class="app-breadcrumb__current" aria-current="page">{{ crumb.title }}</span>
      </li>
    </ol>
  </nav>
</template>

<style scoped>
.app-breadcrumb {
  padding: var(--space-3) var(--space-6) 0;
}

.app-breadcrumb__list {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  width: min(100%, var(--layout-content-max-width));
  margin: 0 auto;
  padding: 0;
  list-style: none;
  color: var(--color-text-subtle);
  font-size: var(--text-xs);
}

.app-breadcrumb__item {
  display: inline-flex;
  align-items: center;
}

.app-breadcrumb__home,
.app-breadcrumb__separator,
.app-breadcrumb__link {
  color: var(--color-text-subtle);
}

.app-breadcrumb__separator {
  padding: 0 var(--space-2);
}

.app-breadcrumb__link {
  border: none;
  background: transparent;
  padding: 0;
  cursor: pointer;
  font: inherit;
}

.app-breadcrumb__home:hover,
.app-breadcrumb__link:hover {
  color: var(--color-primary);
}

.app-breadcrumb__current {
  color: var(--color-text-muted);
  font-weight: 600;
}

@media (max-width: 767px) {
  .app-breadcrumb {
    display: none;
  }
}
</style>
