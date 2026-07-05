<script setup lang="ts">
import ContractPendingState from '@components/ui/ContractPendingState.vue';
</script>

<template>
  <ContractPendingState
    title="法律分类管理"
    description="法律 Agent 当前公开接口清单中没有分类查询、创建、更新或停用接口。前端先展示契约等待状态，避免猜测分类字段和权限语义。"
    :available-endpoints="['POST /sessions（需要 category_code）']"
    :pending-endpoints="[
      'GET /legal-categories',
      'POST /legal-categories',
      'PATCH /legal-categories/{id}',
    ]"
  />
</template>
