<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';

import AppShell from '@app/AppShell.vue';
import ErrorBoundary from '@app/ErrorBoundary.vue';

const route = useRoute();

const isShellDisabled = computed(() => route.meta?.layout === 'plain');
</script>

<template>
  <ErrorBoundary>
    <AppShell v-if="!isShellDisabled" />
    <RouterView v-else />
  </ErrorBoundary>
</template>
