<script setup lang="ts">
import LoginAgentShowcase from './LoginAgentShowcase.vue';
import LoginDynamicPreview from './LoginDynamicPreview.vue';

const emit = defineEmits<{
  (event: 'login'): void;
}>();
</script>

<template>
  <section class="login-product-intro" aria-labelledby="login-product-title">
    <div class="login-product-intro__hero-row">
      <div class="login-product-intro__hero">
        <p class="login-product-intro__eyebrow">
          <span aria-hidden="true" />
          Agent Suite · 企业智能工作台
        </p>

        <h1 id="login-product-title">
          三个 AI 专家
          <strong>一起解决问题</strong>
        </h1>

        <p class="login-product-intro__summary">
          不用在工具之间来回切换。描述目标，系统会把任务交给法律、招聘或数据专家，持续输出可执行的答案。
        </p>

        <div class="login-product-intro__actions">
          <el-button type="primary" size="large" round @click="emit('login')">
            进入工作台
            <span aria-hidden="true">↗</span>
          </el-button>
          <a href="#preview">
            <i aria-hidden="true" />
            查看实时演示
          </a>
        </div>

        <dl class="login-product-intro__proof" aria-label="产品特点">
          <div>
            <dt><el-statistic :value="3" /></dt>
            <dd>专业 Agent</dd>
          </div>
          <div>
            <dt><el-statistic :value="1" /></dt>
            <dd>统一工作入口</dd>
          </div>
          <div>
            <dt><el-statistic :value="24" suffix="/7" /></dt>
            <dd>持续响应</dd>
          </div>
        </dl>
      </div>

      <LoginDynamicPreview />
    </div>

    <LoginAgentShowcase />
  </section>
</template>

<style scoped>
.login-product-intro {
  display: grid;
  gap: clamp(var(--space-8), 6vh, var(--space-16));
  color: var(--login-text);
}

.login-product-intro__hero-row {
  display: grid;
  grid-template-columns: minmax(430px, 0.92fr) minmax(480px, 1.08fr);
  align-items: center;
  gap: clamp(var(--space-8), 6vw, 88px);
  min-height: min(650px, calc(100vh - 188px));
}

.login-product-intro__hero {
  display: grid;
  justify-items: start;
  gap: var(--space-5);
  text-align: left;
}

.login-product-intro__eyebrow {
  display: inline-flex;
  align-items: center;
  gap: var(--space-3);
  margin: 0;
  color: var(--login-text-muted);
  font-size: var(--text-xs);
  font-weight: 750;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.login-product-intro__eyebrow span {
  width: 8px;
  height: 8px;
  background: var(--color-primary);
  border-radius: var(--radius-pill);
  box-shadow: 0 0 0 6px color-mix(in oklch, var(--color-primary) 14%, transparent);
}

.login-product-intro__hero h1 {
  max-width: 690px;
  margin: calc(var(--space-2) * -1) 0;
  padding: var(--space-2) var(--space-2) var(--space-3) 0;
  color: var(--login-text);
  font-size: 4rem;
  font-weight: 760;
  letter-spacing: 0;
  line-height: 1.1;
}

.login-product-intro__hero h1 strong {
  display: block;
  margin-top: var(--space-2);
  color: var(--color-primary);
  font: inherit;
  white-space: nowrap;
}

.login-product-intro__summary {
  max-width: 540px;
  margin: 0;
  color: var(--login-text-muted);
  font-size: var(--text-lg);
  line-height: 1.85;
}

.login-product-intro__actions {
  display: flex;
  align-items: center;
  gap: var(--space-5);
}

.login-product-intro__actions .el-button {
  min-height: 52px;
  padding-inline: var(--space-6);
  border: 0;
  font-weight: 760;
  box-shadow: 0 10px 22px color-mix(in oklch, var(--color-primary) 20%, transparent);
}

.login-product-intro__actions .el-button span {
  margin-left: var(--space-2);
  font-size: var(--text-lg);
}

.login-product-intro__actions a {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--login-text-muted);
  font-size: var(--text-sm);
  font-weight: 700;
  text-decoration: none;
  transition: color var(--duration-fast) var(--ease-in-out);
}

.login-product-intro__actions a i {
  width: 9px;
  height: 9px;
  background: var(--login-accent);
  border-radius: var(--radius-pill);
}

.login-product-intro__actions a:hover {
  color: var(--login-text);
}

.login-product-intro__proof {
  display: flex;
  gap: clamp(var(--space-5), 4vw, var(--space-10));
  margin: var(--space-4) 0 0;
  padding: var(--space-5) 0 0;
  border-top: 1px solid var(--login-border);
}

.login-product-intro__proof div {
  display: grid;
  gap: 2px;
}

.login-product-intro__proof dt {
  font-family: var(--font-mono);
  font-size: var(--text-xl);
  font-weight: 800;
}

.login-product-intro__proof :deep(.el-statistic__content) {
  color: var(--login-text);
  font-family: var(--font-mono);
  font-size: var(--text-xl);
  font-weight: 800;
}

.login-product-intro__proof dd {
  margin: 0;
  color: var(--login-text-subtle);
  font-size: var(--text-xs);
}

@media (max-width: 1100px) {
  .login-product-intro__hero-row {
    grid-template-columns: 1fr;
    min-height: auto;
  }
}

@media (max-width: 767px) {
  .login-product-intro {
    gap: var(--space-10);
  }

  .login-product-intro__hero-row {
    gap: var(--space-8);
  }

  .login-product-intro__hero h1 {
    font-size: 3rem;
    letter-spacing: 0;
    line-height: 1.12;
  }

  .login-product-intro__summary {
    font-size: var(--text-base);
  }

  .login-product-intro__actions {
    align-items: flex-start;
    flex-direction: column;
    gap: var(--space-4);
  }

  .login-product-intro__proof {
    width: 100%;
    justify-content: space-between;
    gap: var(--space-3);
  }
}
</style>
