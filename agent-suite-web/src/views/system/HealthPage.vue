<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';

import { dataApi, legalApi, recruitmentApi, suiteEnv } from '@lib/config';
import {
  buildWebConfigHealthItems,
  createCheckingSnapshot,
  probeServiceHealth,
} from '@lib/service-health';
import type { HealthProbeClient, ServiceHealthSnapshot, ServiceHealthTarget } from '@/types/health';

interface HealthTargetBinding {
  target: ServiceHealthTarget;
  client: HealthProbeClient;
}

const targets: HealthTargetBinding[] = [
  {
    target: {
      id: 'legal',
      label: '法律咨询 Agent',
      modulePrefix: suiteEnv.legalPrefix,
      livePath: '/health/live',
    },
    client: legalApi,
  },
  {
    target: {
      id: 'recruitment',
      label: '智能招聘 Agent',
      modulePrefix: suiteEnv.recruitmentPrefix,
      livePath: '/health/live',
    },
    client: recruitmentApi,
  },
  {
    target: {
      id: 'data',
      label: '智能问数 Agent',
      modulePrefix: suiteEnv.dataPrefix,
      livePath: '/health/live',
    },
    client: dataApi,
  },
];

const snapshots = ref<ServiceHealthSnapshot[]>(
  targets.map(({ target }) => createCheckingSnapshot(target)),
);
const configItems = computed(() => buildWebConfigHealthItems(suiteEnv));
const isChecking = computed(() => snapshots.value.some((item) => item.status === 'checking'));

async function probe(): Promise<void> {
  snapshots.value = targets.map(({ target }) => createCheckingSnapshot(target));
  snapshots.value = await Promise.all(
    targets.map(({ target, client }) => probeServiceHealth(target, client)),
  );
}

onMounted(() => {
  void probe();
});
</script>

<template>
  <div class="health-page">
    <section class="health-page__hero" aria-labelledby="health-title">
      <div>
        <p class="health-page__eyebrow">WEB-421</p>
        <h1 id="health-title">系统健康</h1>
        <p class="health-page__description">
          检查统一前端配置与三个 Agent 的公开健康端点。服务下线时仅对应模块降级，
          不影响其它模块入口。
        </p>
      </div>
      <el-button type="primary" :loading="isChecking" @click="probe">重新检测</el-button>
    </section>

    <section class="health-page__section" aria-labelledby="services-title">
      <h2 id="services-title">Agent 服务状态</h2>
      <div class="health-page__grid">
        <article
          v-for="snapshot in snapshots"
          :key="snapshot.id"
          class="health-card"
          :class="`health-card--${snapshot.status}`"
        >
          <div class="health-card__header">
            <div>
              <h3>{{ snapshot.label }}</h3>
              <p>{{ snapshot.modulePrefix }}{{ snapshot.livePath }}</p>
            </div>
            <el-tag
              :type="
                snapshot.status === 'healthy'
                  ? 'success'
                  : snapshot.status === 'degraded'
                    ? 'warning'
                    : snapshot.status === 'checking'
                      ? 'info'
                      : 'danger'
              "
              effect="light"
            >
              {{ snapshot.status }}
            </el-tag>
          </div>
          <dl class="health-card__details">
            <div>
              <dt>检查时间</dt>
              <dd>{{ snapshot.checkedAt ?? '尚未完成' }}</dd>
            </div>
            <div>
              <dt>返回详情</dt>
              <dd>
                <code>{{ snapshot.detail }}</code>
              </dd>
            </div>
          </dl>
        </article>
      </div>
    </section>

    <section class="health-page__section" aria-labelledby="config-title">
      <h2 id="config-title">前端运行配置</h2>
      <el-table :data="configItems" class="health-page__config-table" row-key="key">
        <el-table-column prop="label" label="配置项" min-width="180" />
        <el-table-column prop="value" label="当前值" min-width="220">
          <template #default="{ row }">
            <code>{{ row.value }}</code>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="row.status === 'ok' ? 'success' : 'warning'" effect="light">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="detail" label="说明" min-width="240" />
      </el-table>
    </section>
  </div>
</template>

<style scoped>
.health-page {
  max-width: var(--layout-content-max-width);
  margin: var(--space-8) auto;
  padding: 0 var(--space-2) var(--space-8);
}

.health-page__hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-6);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
}

.health-page__eyebrow {
  margin-bottom: var(--space-2);
  color: var(--color-primary);
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.08em;
}

.health-page__description {
  max-width: 760px;
  margin-top: var(--space-3);
  color: var(--color-text-muted);
}

.health-page__section {
  margin-top: var(--space-6);
}

.health-page__section h2 {
  margin-bottom: var(--space-3);
  font-size: var(--text-xl);
}

.health-page__grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--space-4);
}

.health-card {
  min-width: 0;
  padding: var(--space-4);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
}

.health-card--healthy {
  border-color: var(--color-success);
}

.health-card--degraded {
  border-color: var(--color-warning);
}

.health-card--down {
  border-color: var(--color-danger);
}

.health-card__header {
  display: flex;
  justify-content: space-between;
  gap: var(--space-3);
}

.health-card__header h3 {
  font-size: var(--text-lg);
}

.health-card__header p,
.health-card__details {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.health-card__details {
  display: grid;
  gap: var(--space-3);
  margin: var(--space-4) 0 0;
}

.health-card__details div {
  min-width: 0;
}

.health-card__details dt {
  margin-bottom: var(--space-1);
  font-weight: 600;
  color: var(--color-text);
}

.health-card__details dd {
  min-width: 0;
  margin: 0;
  overflow-wrap: anywhere;
}

.health-page__config-table {
  width: 100%;
}

code {
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

@media (max-width: 1023px) {
  .health-page__grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 767px) {
  .health-page {
    margin-top: var(--space-4);
  }

  .health-page__hero {
    flex-direction: column;
    padding: var(--space-4);
  }
}
</style>
