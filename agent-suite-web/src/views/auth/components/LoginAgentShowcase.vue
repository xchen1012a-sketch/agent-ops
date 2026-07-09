<script setup lang="ts">
import AppIcon from '@components/ui/AppIcon.vue';

const agentCards = [
  {
    index: '01',
    icon: 'ChatDotRound',
    tone: 'legal',
    title: '法律专家',
    description: '拆解合同与劳动争议，识别风险并给出处理路径。',
    metric: '咨询 · 合同 · 维权',
  },
  {
    index: '02',
    icon: 'User',
    tone: 'recruit',
    title: '招聘专家',
    description: '从简历筛选到面试提纲，建立一致的评估标准。',
    metric: '筛选 · 面试 · 匹配',
  },
  {
    index: '03',
    icon: 'DataAnalysis',
    tone: 'data',
    title: '数据专家',
    description: '把自然语言转成分析，快速找到趋势、排行与异常。',
    metric: '趋势 · 排行 · 异常',
  },
] as const;
</script>

<template>
  <section id="assistants" class="login-agent-showcase" aria-labelledby="login-agent-title">
    <div class="login-agent-showcase__header">
      <p>能力矩阵 / 03</p>
      <h2 id="login-agent-title">同一个入口，不同领域自动接力。</h2>
    </div>
    <div class="login-agent-showcase__grid">
      <el-card
        v-for="card in agentCards"
        :key="card.title"
        class="login-agent-showcase__card"
        :class="`login-agent-showcase__card--${card.tone}`"
        shadow="hover"
      >
        <span class="login-agent-showcase__index">{{ card.index }}</span>
        <span class="login-agent-showcase__icon" aria-hidden="true">
          <AppIcon :name="card.icon" />
        </span>
        <div class="login-agent-showcase__copy">
          <p>{{ card.metric }}</p>
          <h3>{{ card.title }}</h3>
          <span>{{ card.description }}</span>
        </div>
        <i class="login-agent-showcase__arrow" aria-hidden="true">↗</i>
      </el-card>
    </div>
  </section>
</template>

<style scoped>
.login-agent-showcase {
  display: grid;
  gap: var(--space-5);
  padding-bottom: var(--space-12);
}
.login-agent-showcase__header {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: var(--space-5);
  text-align: left;
}
.login-agent-showcase__header p {
  margin: 0;
  color: var(--login-accent);
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.12em;
  white-space: nowrap;
}
.login-agent-showcase__header h2 {
  margin: 0;
  color: var(--login-text);
  font-size: var(--text-2xl);
  letter-spacing: 0;
}
.login-agent-showcase__grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--space-3);
}
.login-agent-showcase__card {
  position: relative;
  min-height: 202px;
  overflow: hidden;
  background: var(--login-surface);
  border: 1px solid var(--login-border);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
  transition:
    background-color var(--duration-normal) var(--ease-in-out),
    border-color var(--duration-normal) var(--ease-in-out),
    transform var(--duration-normal) var(--ease-out-expo);
}
.login-agent-showcase__card :deep(.el-card__body) {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: start;
  gap: var(--space-4);
  min-height: 202px;
  padding: var(--space-6);
}
.login-agent-showcase__card:hover {
  background: var(--login-surface-strong);
  border-color: var(--login-border-strong);
}
.login-agent-showcase__index {
  position: absolute;
  top: var(--space-4);
  right: var(--space-4);
  color: var(--login-text-subtle);
  font-family: var(--font-mono);
  font-size: var(--text-xs);
}
.login-agent-showcase__icon {
  display: grid;
  place-items: center;
  width: 42px;
  height: 42px;
  border: 1px solid currentColor;
  border-radius: var(--radius-md);
}
.login-agent-showcase__card--legal .login-agent-showcase__icon {
  color: var(--color-legal);
  background: color-mix(in oklch, var(--color-legal) 12%, transparent);
}
.login-agent-showcase__card--recruit .login-agent-showcase__icon {
  color: var(--color-recruit);
  background: color-mix(in oklch, var(--color-recruit) 12%, transparent);
}
.login-agent-showcase__card--data .login-agent-showcase__icon {
  color: var(--color-data);
  background: color-mix(in oklch, var(--color-data) 12%, transparent);
}
.login-agent-showcase__copy {
  display: grid;
  gap: var(--space-2);
  padding-top: var(--space-1);
}
.login-agent-showcase__copy p {
  margin: 0;
  color: var(--login-text-subtle);
  font-family: var(--font-mono);
  font-size: 0.6875rem;
}
.login-agent-showcase__copy h3 {
  margin: 0;
  color: var(--login-text);
  font-size: var(--text-lg);
}
.login-agent-showcase__copy span {
  color: var(--login-text-muted);
  line-height: var(--line-relaxed);
}
.login-agent-showcase__arrow {
  align-self: end;
  color: var(--login-text-subtle);
  font-style: normal;
}
@media (max-width: 900px) {
  .login-agent-showcase__header {
    display: grid;
    gap: var(--space-2);
  }
  .login-agent-showcase__grid {
    grid-template-columns: 1fr;
  }
  .login-agent-showcase__card {
    min-height: 164px;
  }
  .login-agent-showcase__card :deep(.el-card__body) {
    min-height: 164px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .login-agent-showcase__card {
    transition: none;
  }

  .login-agent-showcase__card:hover {
    transform: none;
  }
}
</style>
