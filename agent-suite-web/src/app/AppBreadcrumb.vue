<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';

import { router } from '@router/index';

const route = useRoute();

interface Crumb {
  title: string;
  to?: string;
}

const crumbs = computed<Crumb[]>(() => {
  const title = route.meta?.title;
  const module = route.meta?.module;
  const list: Crumb[] = [];
  if (module === 'legal') {
    list.push({ title: '法律咨询', to: '/legal' });
  } else if (module === 'recruitment') {
    list.push({ title: '智能招聘', to: '/recruitment' });
  } else if (module === 'data') {
    list.push({ title: '智能问数', to: '/data' });
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
  <nav class="app-breadcrumb" aria-label="面包屑">
    <ol class="app-breadcrumb__list">
      <li>
        <RouterLink to="/" class="app-breadcrumb__home"> 首页 </RouterLink>
      </li>
      <li v-for="(crumb, index) in crumbs" :key="index" aria-current="page">
        <span class="app-breadcrumb__separator">/</span>
        <button
          v-if="crumb.to"
          type="button"
          class="app-breadcrumb__link"
          @click="navigate(crumb.to)"
        >
          {{ crumb.title }}
        </button>
        <span v-else class="app-breadcrumb__current">{{ crumb.title }}</span>
      </li>
    </ol>
  </nav>
</template>

<style scoped>
.app-breadcrumb {
  padding: var(--space-2) var(--space-4);
  background-color: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}

.app-breadcrumb__list {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2);
  margin: 0;
  padding: 0;
  list-style: none;
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.app-breadcrumb__home {
  color: var(--color-text-muted);
}

.app-breadcrumb__separator {
  color: var(--color-text-muted);
}

.app-breadcrumb__link {
  border: none;
  background: transparent;
  color: var(--color-text-muted);
  padding: 0;
  cursor: pointer;
  font: inherit;
}

.app-breadcrumb__link:hover {
  color: var(--color-primary);
}

.app-breadcrumb__current {
  color: var(--color-text);
  font-weight: 600;
}
</style>
