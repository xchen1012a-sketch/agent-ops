<script setup lang="ts">
import ContractPendingState from '@components/ui/ContractPendingState.vue';
</script>

<template>
  <ContractPendingState
    title="用户管理"
    description="统一认证由 auth 模块负责，法律 Agent 当前仅信任上游 x-user-public-id，不公开法律模块用户管理接口。前端不在法律模块内实现用户增删改。"
    :available-endpoints="['法律 Agent 请求头：x-user-public-id']"
    :pending-endpoints="['由统一认证模块提供用户列表、角色修改、禁用/启用接口']"
  />
</template>
