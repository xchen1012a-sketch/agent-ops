<script setup lang="ts">
import ContractPendingState from '@components/ui/ContractPendingState.vue';
</script>

<template>
  <ContractPendingState
    title="知识材料管理"
    description="法律知识材料元数据已在后端数据层设计中出现，但当前公开 API 未提供上传、列表、索引状态或版本管理接口。前端不直接上传文件或猜测字段。"
    :available-endpoints="['GET /health/ready（仅健康检查）']"
    :pending-endpoints="[
      'GET /admin/knowledge-materials',
      'POST /admin/knowledge-materials',
      'PATCH /admin/knowledge-materials/{id}',
      'POST /admin/knowledge-materials/{id}/reindex',
    ]"
  />
</template>
