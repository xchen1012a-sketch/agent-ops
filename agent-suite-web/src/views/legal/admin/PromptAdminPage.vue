<script setup lang="ts">
import ContractPendingState from '@components/ui/ContractPendingState.vue';
</script>

<template>
  <ContractPendingState
    title="Prompt 版本管理"
    description="法律 Prompt 版本在后端数据层中有持久化模型，但当前公开 API 未提供版本列表、创建、激活或退役接口。前端保持只读契约等待状态。"
    :pending-endpoints="[
      'GET /admin/prompt-versions',
      'POST /admin/prompt-versions',
      'POST /admin/prompt-versions/{id}/activate',
      'POST /admin/prompt-versions/{id}/retire',
    ]"
  />
</template>
