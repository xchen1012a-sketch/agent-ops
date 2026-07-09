<script setup lang="ts">
import { useRoute } from 'vue-router';

import EmptyState from '@components/ui/EmptyState.vue';

const route = useRoute();
</script>

<template>
  <EmptyState
    :title="String(route.meta.title ?? '页面占位')"
    description="该模块将在后续迭代中开放。当前为前端壳层占位页，对应后端服务就绪后即可联调。"
    icon="DocumentRemove"
  />
</template>
