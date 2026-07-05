<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';

import AppIcon from '@components/ui/AppIcon.vue';
import SSEStatusIndicator from '@components/ui/SSEStatusIndicator.vue';

const agents = [
  { tone: 'legal', label: '法律专家', icon: 'ChatDotRound' },
  { tone: 'recruit', label: '招聘专家', icon: 'User' },
  { tone: 'data', label: '数据专家', icon: 'DataAnalysis' },
] as const;

const streamingDemos = [
  {
    question: '帮我看看合同违约责任是否合理',
    answer: '我会先定位违约条款，再判断责任是否过重，最后整理一版可直接沟通的处理建议。',
    highlights: ['定位条款', '判断风险', '生成建议'],
  },
  {
    question: '帮我筛选适合的 Java 后端候选人',
    answer: '我会核对项目经验、技术栈与岗位要求，再整理候选人重点和结构化面试提纲。',
    highlights: ['解析简历', '对齐要求', '生成提纲'],
  },
  {
    question: '本周销售额最高的商品有哪些',
    answer: '我会理解统计口径，完成安全查询，再生成销售排行、变化趋势和可执行结论。',
    highlights: ['理解指标', '安全查询', '生成结论'],
  },
] as const;

const activeAgentIndex = ref(0);
const typedQuestion = ref('');
const typedAnswer = ref('');
const isAnswerStreaming = ref(false);
const hasAnswerFinished = ref(false);
let timers: number[] = [];

const activeAgent = computed(() => agents[activeAgentIndex.value]);
const activeDemo = computed(() => streamingDemos[activeAgentIndex.value]);
const questionFinished = computed(
  () => typedQuestion.value.length === activeDemo.value.question.length,
);

function clearTimers(): void {
  timers.forEach((timer) => window.clearTimeout(timer));
  timers = [];
}

function schedule(callback: () => void, delay: number): void {
  timers.push(window.setTimeout(callback, delay));
}

function playStreamingDemo(): void {
  clearTimers();
  typedQuestion.value = '';
  typedAnswer.value = '';
  isAnswerStreaming.value = false;
  hasAnswerFinished.value = false;
  const demo = activeDemo.value;

  Array.from(demo.question).forEach((char, index) => {
    schedule(() => {
      typedQuestion.value += char;
    }, 82 * index);
  });

  const answerStartDelay = demo.question.length * 82 + 460;
  schedule(() => {
    isAnswerStreaming.value = true;
  }, answerStartDelay);

  Array.from(demo.answer).forEach((char, index) => {
    schedule(
      () => {
        typedAnswer.value += char;
      },
      answerStartDelay + index * 34,
    );
  });

  const answerEndDelay = answerStartDelay + demo.answer.length * 34;
  schedule(() => {
    isAnswerStreaming.value = false;
    hasAnswerFinished.value = true;
  }, answerEndDelay + 180);
  schedule(() => {
    activeAgentIndex.value = (activeAgentIndex.value + 1) % agents.length;
    playStreamingDemo();
  }, answerEndDelay + 2800);
}

onMounted(playStreamingDemo);
onBeforeUnmount(clearTimers);
</script>

<template>
  <section id="preview" class="login-dynamic-preview" aria-label="实时协同演示">
    <div class="login-dynamic-preview__window">
      <header class="login-dynamic-preview__header">
        <div class="login-dynamic-preview__chrome" aria-hidden="true"><span /><span /><span /></div>
        <p>LIVE WORKFLOW</p>
        <SSEStatusIndicator state="open" />
      </header>

      <nav class="login-dynamic-preview__agents" aria-label="可用 AI 专家">
        <el-tag
          v-for="(agent, index) in agents"
          :key="agent.label"
          :class="[
            `login-dynamic-preview__agent--${agent.tone}`,
            { 'is-active': index === activeAgentIndex },
          ]"
          effect="plain"
          round
        >
          <AppIcon :name="agent.icon" />
          {{ agent.label }}
        </el-tag>
      </nav>

      <div class="login-dynamic-preview__workspace">
        <div class="login-dynamic-preview__request">
          <span class="login-dynamic-preview__meta">
            USER REQUEST / 0{{ activeAgentIndex + 1 }}
          </span>
          <p>
            {{ typedQuestion }}
            <i class="login-dynamic-preview__cursor" aria-hidden="true" />
          </p>
        </div>

        <div class="login-dynamic-preview__connector" aria-hidden="true"><span /><i /><span /></div>

        <div class="login-dynamic-preview__response">
          <div class="login-dynamic-preview__response-head">
            <span
              class="login-dynamic-preview__agent-avatar"
              :class="`login-dynamic-preview__agent-avatar--${activeAgent.tone}`"
            >
              <AppIcon :name="activeAgent.icon" />
            </span>
            <span>
              <strong>{{ activeAgent.label }}</strong>
              <small>正在分析任务</small>
            </span>
            <i class="login-dynamic-preview__pulse" aria-hidden="true" />
          </div>

          <div class="login-dynamic-preview__answer">
            <p>
              {{ typedAnswer }}
              <i
                v-if="isAnswerStreaming"
                class="login-dynamic-preview__answer-cursor"
                aria-hidden="true"
              />
            </p>
            <div
              class="login-dynamic-preview__thinking"
              :class="{
                'login-dynamic-preview__thinking--visible': questionFinished && !typedAnswer,
              }"
              aria-hidden="true"
            >
              <span /><span /><span />
            </div>
          </div>

          <div
            class="login-dynamic-preview__steps"
            :class="{ 'login-dynamic-preview__steps--done': hasAnswerFinished }"
            aria-label="分析步骤"
          >
            <span v-for="(highlight, index) in activeDemo.highlights" :key="highlight">
              <i>{{ index + 1 }}</i>
              {{ highlight }}
            </span>
          </div>
        </div>
      </div>

      <footer class="login-dynamic-preview__footer">
        <span><i aria-hidden="true" /> 系统已自动路由至{{ activeAgent.label }}</span>
        <span class="login-dynamic-preview__send" aria-hidden="true">
          <AppIcon name="Expand" />
        </span>
      </footer>
    </div>
  </section>
</template>

<style scoped>
.login-dynamic-preview {
  position: relative;
  width: min(100%, 600px);
  justify-self: end;
}
.login-dynamic-preview__window {
  position: relative;
  display: grid;
  gap: var(--space-4);
  min-height: 570px;
  padding: var(--space-5);
  overflow: hidden;
  background: color-mix(in oklch, var(--color-surface) 92%, transparent);
  border: 1px solid var(--login-border-strong);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
}
.login-dynamic-preview__header {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  min-height: 28px;
}
.login-dynamic-preview__header p {
  margin: 0;
  color: var(--login-text-subtle);
  font-family: var(--font-mono);
  font-size: 0.625rem;
  letter-spacing: 0.16em;
}
.login-dynamic-preview__chrome {
  display: flex;
  gap: 6px;
}
.login-dynamic-preview__chrome span {
  width: 7px;
  height: 7px;
  background: var(--login-border-strong);
  border-radius: var(--radius-pill);
}
.login-dynamic-preview__header :deep(.sse-status) {
  justify-self: end;
}
.login-dynamic-preview__agents {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--space-2);
}
.login-dynamic-preview__agents > .el-tag {
  --el-tag-text-color: var(--login-text-muted);
  --el-tag-bg-color: var(--color-surface);
  --el-tag-border-color: var(--color-border);

  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  min-height: 40px;
  color: var(--login-text-muted);
  background: var(--login-surface);
  border: 1px solid var(--login-border);
  border-radius: var(--radius-md);
  font-size: var(--text-xs);
  font-weight: 700;
}
.login-dynamic-preview__agent--legal {
  --el-tag-text-color: var(--color-legal);
  --el-tag-border-color: color-mix(in oklch, var(--color-legal) 35%, var(--color-border));

  color: var(--color-legal) !important;
  border-color: color-mix(in oklch, var(--color-legal) 35%, transparent) !important;
}
.login-dynamic-preview__agent--legal.is-active {
  --el-tag-bg-color: var(--color-legal-soft);

  background: var(--color-legal-soft);
}
.login-dynamic-preview__agent--recruit {
  --el-tag-text-color: var(--color-recruit);
  --el-tag-border-color: color-mix(in oklch, var(--color-recruit) 35%, var(--color-border));
}
.login-dynamic-preview__agent--recruit.is-active {
  --el-tag-bg-color: var(--color-recruit-soft);

  background: var(--color-recruit-soft);
}
.login-dynamic-preview__agent--data {
  --el-tag-text-color: var(--color-data);
  --el-tag-border-color: color-mix(in oklch, var(--color-data) 35%, var(--color-border));
}
.login-dynamic-preview__agent--data.is-active {
  --el-tag-bg-color: var(--color-data-soft);

  background: var(--color-data-soft);
}
.login-dynamic-preview__agents > .el-tag.is-active {
  box-shadow: var(--shadow-card);
}
.login-dynamic-preview__workspace {
  display: grid;
  grid-template-rows: 88px 24px 1fr;
  min-height: 384px;
  padding: var(--space-4);
  background: color-mix(in oklch, var(--color-surface-muted), var(--color-surface) 28%);
  border: 1px solid var(--login-border);
  border-radius: var(--radius-lg);
}
.login-dynamic-preview__meta {
  color: var(--login-text-subtle);
  font-family: var(--font-mono);
  font-size: 0.625rem;
  letter-spacing: 0.1em;
}
.login-dynamic-preview__request {
  display: grid;
  align-content: start;
  gap: var(--space-2);
}
.login-dynamic-preview__request p {
  height: 46px;
  margin: 0;
  padding: var(--space-3) var(--space-4);
  overflow: hidden;
  color: var(--color-primary-active);
  background: var(--color-primary-soft);
  border: 1px solid color-mix(in oklch, var(--login-accent) 28%, var(--login-border));
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: 650;
  white-space: nowrap;
}
.login-dynamic-preview__cursor,
.login-dynamic-preview__answer-cursor {
  display: inline-block;
  width: 1px;
  height: 1em;
  margin-left: 2px;
  vertical-align: -0.12em;
  background: currentColor;
  animation: login-cursor 800ms steps(1) infinite;
}
.login-dynamic-preview__connector {
  display: flex;
  align-items: center;
  gap: 7px;
  padding-left: var(--space-5);
}
.login-dynamic-preview__connector span {
  width: 4px;
  height: 4px;
  background: var(--login-accent);
  border-radius: var(--radius-pill);
}
.login-dynamic-preview__connector i {
  width: 40px;
  height: 1px;
  background: linear-gradient(90deg, var(--login-accent), transparent);
}
.login-dynamic-preview__response {
  display: grid;
  grid-template-rows: 46px 112px 40px;
  gap: var(--space-3);
  padding: var(--space-4);
  background: var(--color-surface);
  border: 1px solid var(--login-border);
  border-radius: var(--radius-lg);
}
.login-dynamic-preview__response-head {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}
.login-dynamic-preview__agent-avatar {
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  border-radius: var(--radius-md);
}
.login-dynamic-preview__agent-avatar--legal {
  color: var(--color-legal);
  background: var(--color-legal-soft);
  border: 1px solid color-mix(in oklch, var(--color-legal) 36%, var(--color-border));
}
.login-dynamic-preview__agent-avatar--recruit {
  color: var(--color-recruit);
  background: var(--color-recruit-soft);
  border: 1px solid color-mix(in oklch, var(--color-recruit) 36%, var(--color-border));
}
.login-dynamic-preview__agent-avatar--data {
  color: var(--color-data);
  background: var(--color-data-soft);
  border: 1px solid color-mix(in oklch, var(--color-data) 36%, var(--color-border));
}
.login-dynamic-preview__response-head > span:nth-child(2) {
  display: grid;
  gap: 1px;
}
.login-dynamic-preview__response-head strong {
  color: var(--login-text);
  font-size: var(--text-sm);
}
.login-dynamic-preview__response-head small {
  color: var(--login-text-subtle);
  font-size: 0.6875rem;
}
.login-dynamic-preview__pulse {
  width: 7px;
  height: 7px;
  margin-left: auto;
  background: var(--login-accent);
  border-radius: var(--radius-pill);
  box-shadow: 0 0 0 6px color-mix(in oklch, var(--login-accent) 12%, transparent);
  animation: login-pulse 1.8s var(--ease-in-out) infinite;
}
.login-dynamic-preview__answer {
  position: relative;
  height: 112px;
  padding: var(--space-3);
  overflow: hidden;
  color: var(--login-text-muted);
  background: var(--color-surface-muted);
  border: 1px solid var(--login-border);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  line-height: var(--line-relaxed);
}
.login-dynamic-preview__answer p {
  margin: 0;
}
.login-dynamic-preview__answer-cursor {
  color: var(--login-accent);
}
.login-dynamic-preview__thinking {
  position: absolute;
  top: var(--space-4);
  left: var(--space-4);
  display: flex;
  gap: 5px;
  opacity: 0;
  transition: opacity var(--duration-fast) var(--ease-in-out);
}
.login-dynamic-preview__thinking--visible {
  opacity: 1;
}
.login-dynamic-preview__thinking span {
  width: 5px;
  height: 5px;
  background: var(--login-accent);
  border-radius: var(--radius-pill);
  animation: login-dots 1s var(--ease-in-out) infinite;
}
.login-dynamic-preview__thinking span:nth-child(2) {
  animation-delay: 140ms;
}
.login-dynamic-preview__thinking span:nth-child(3) {
  animation-delay: 280ms;
}
.login-dynamic-preview__steps {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-2);
  opacity: 0.42;
  transition: opacity var(--duration-normal) var(--ease-in-out);
}
.login-dynamic-preview__steps--done {
  opacity: 1;
}
.login-dynamic-preview__steps span {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--login-text-muted);
  font-size: 0.6875rem;
  white-space: nowrap;
}
.login-dynamic-preview__steps i {
  display: grid;
  place-items: center;
  width: 20px;
  height: 20px;
  color: var(--login-accent);
  border: 1px solid color-mix(in oklch, var(--login-accent) 44%, transparent);
  border-radius: var(--radius-pill);
  font-family: var(--font-mono);
  font-size: 0.625rem;
  font-style: normal;
}
.login-dynamic-preview__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  min-height: 48px;
  padding: 0 6px 0 var(--space-3);
  color: var(--login-text-subtle);
  border: 1px solid var(--login-border);
  border-radius: var(--radius-pill);
  font-size: var(--text-xs);
}
.login-dynamic-preview__footer > span:first-child {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
}
.login-dynamic-preview__footer > span:first-child i {
  width: 5px;
  height: 5px;
  background: var(--login-accent);
  border-radius: var(--radius-pill);
}
.login-dynamic-preview__send {
  display: grid;
  flex: 0 0 auto;
  place-items: center;
  width: 36px;
  height: 36px;
  color: var(--login-text);
  background: var(--color-primary);
  border-radius: var(--radius-pill);
}

@keyframes login-cursor {
  0%,
  48% {
    opacity: 1;
  }
  49%,
  100% {
    opacity: 0;
  }
}
@keyframes login-pulse {
  50% {
    opacity: 0.45;
    transform: scale(0.78);
  }
}
@keyframes login-dots {
  50% {
    opacity: 0.35;
    transform: translateY(-3px);
  }
}

@media (max-width: 1100px) {
  .login-dynamic-preview {
    justify-self: stretch;
    width: min(100%, 720px);
  }
}
@media (max-width: 767px) {
  .login-dynamic-preview__window {
    min-height: 536px;
    padding: var(--space-3);
  }
  .login-dynamic-preview__header {
    grid-template-columns: 1fr 1fr;
  }
  .login-dynamic-preview__header p {
    display: none;
  }
  .login-dynamic-preview__agents > .el-tag {
    font-size: 0;
  }
  .login-dynamic-preview__agents > .el-tag :deep(svg) {
    font-size: var(--text-base);
  }
  .login-dynamic-preview__steps span {
    gap: 3px;
    font-size: 0.625rem;
  }
  .login-dynamic-preview__workspace {
    padding: var(--space-3);
  }
}

@media (prefers-reduced-motion: reduce) {
  .login-dynamic-preview__cursor,
  .login-dynamic-preview__answer-cursor,
  .login-dynamic-preview__pulse,
  .login-dynamic-preview__thinking span {
    animation: none;
  }
}
</style>
