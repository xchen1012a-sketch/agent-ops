<script setup lang="ts">
import { onMounted, ref } from 'vue';

import { legalApi } from '@lib/config';

interface HealthSnapshot {
  status: 'checking' | 'healthy' | 'degraded' | 'down';
  checkedAt: string | null;
  detail: string;
}

const snapshot = ref<HealthSnapshot>({
  status: 'checking',
  checkedAt: null,
  detail: '',
});

async function probe(): Promise<void> {
  snapshot.value = { ...snapshot.value, status: 'checking' };
  try {
    const { data, status } = await legalApi.get('/health/live', {
      validateStatus: (code) => code < 500,
    });
    snapshot.value = {
      status: status >= 200 && status < 300 ? 'healthy' : 'degraded',
      checkedAt: new Date().toISOString(),
      detail: typeof data === 'string' ? data : JSON.stringify(data),
    };
  } catch (error) {
    snapshot.value = {
      status: 'down',
      checkedAt: new Date().toISOString(),
      detail: error instanceof Error ? error.message : String(error),
    };
  }
}

onMounted(() => {
  void probe();
});
</script>

<template>
  <div class="health-page">
    <h1>系统健康</h1>
    <p>显示各模块当前可用状态。</p>
    <el-descriptions :column="1" border>
      <el-descriptions-item label="检查时间">
        {{ snapshot.checkedAt ?? '-' }}
      </el-descriptions-item>
      <el-descriptions-item label="法律 Agent /health/live">
        <el-tag
          :type="
            snapshot.status === 'healthy'
              ? 'success'
              : snapshot.status === 'checking'
                ? 'info'
                : 'danger'
          "
        >
          {{ snapshot.status }}
        </el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="详情">
        <code>{{ snapshot.detail || '-' }}</code>
      </el-descriptions-item>
    </el-descriptions>
    <el-button class="health-page__refresh" @click="probe"> 重新检测 </el-button>
  </div>
</template>

<style scoped>
.health-page {
  max-width: 720px;
  margin: var(--space-8) auto;
  padding: var(--space-6);
}

.health-page__refresh {
  margin-top: var(--space-4);
}
</style>
