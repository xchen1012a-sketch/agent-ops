<script setup lang="ts">
import { computed, ref } from 'vue';
import { useRoute } from 'vue-router';

import AppHeader from './AppHeader.vue';
import AppSidebar from './AppSidebar.vue';
import ErrorBoundary from './ErrorBoundary.vue';
import GlobalToast from './GlobalToast.vue';

const route = useRoute();
const sidebarCollapsed = ref(false);
const loadingLabel = '\u6b63\u5728\u6253\u5f00\u667a\u80fd\u5de5\u4f5c\u53f0\u2026';

const currentModule = computed(() => (route.meta?.module ?? null) as string | null);

function toggleSidebar(): void {
  sidebarCollapsed.value = !sidebarCollapsed.value;
}
</script>

<template>
  <div
    class="app-shell"
    :class="{
      'app-shell--collapsed': sidebarCollapsed,
      [`app-shell--module-${currentModule}`]: Boolean(currentModule),
    }"
  >
    <AppSidebar :collapsed="sidebarCollapsed" @toggle="toggleSidebar" />
    <div class="app-shell__main">
      <AppHeader :sidebar-collapsed="sidebarCollapsed" @toggle-sidebar="toggleSidebar" />
      <main class="app-shell__content" role="main">
        <div class="app-shell__content-inner">
          <ErrorBoundary>
            <RouterView v-slot="{ Component }">
              <Transition name="app-view" mode="out-in" appear>
                <Suspense>
                  <component :is="Component" />
                  <template #fallback>
                    <div class="app-shell__loading" role="status" aria-live="polite">
                      <span class="app-shell__loading-mark" aria-hidden="true" />
                      <span>{{ loadingLabel }}</span>
                    </div>
                  </template>
                </Suspense>
              </Transition>
            </RouterView>
          </ErrorBoundary>
        </div>
      </main>
    </div>
    <GlobalToast />
  </div>
</template>

<style scoped>
.app-shell {
  display: grid;
  grid-template-columns: var(--layout-sidebar-width) minmax(0, 1fr);
  min-height: 100vh;
  background:
    linear-gradient(
      180deg,
      color-mix(in oklch, var(--color-bg), var(--color-surface) 42%),
      var(--color-bg)
    ),
    var(--color-bg);
  transition: grid-template-columns var(--duration-normal) var(--ease-in-out);
}

.app-shell--collapsed {
  grid-template-columns: 0 minmax(0, 1fr);
}

.app-shell__main {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.app-shell__content {
  flex: 1 1 auto;
  padding: var(--space-5) var(--space-6) var(--space-8);
}

.app-shell__content-inner {
  width: min(100%, var(--layout-content-max-width));
  margin: 0 auto;
}

/* Claude-style route cross-fade: leave fast, enter with a gentle rise. */
.app-view-enter-active {
  transition:
    opacity var(--duration-normal) var(--ease-out-expo),
    transform var(--duration-normal) var(--ease-out-expo);
}

.app-view-leave-active {
  transition: opacity var(--duration-fast) var(--ease-in-out);
}

.app-view-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.app-view-leave-to {
  opacity: 0;
}

.app-shell__loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  min-height: 280px;
  color: var(--color-text-muted);
}

.app-shell__loading-mark {
  width: 12px;
  height: 12px;
  border-radius: var(--radius-pill);
  background: var(--color-primary);
  box-shadow: 0 0 0 8px var(--color-primary-soft);
  animation: app-shell-loading-pulse 1.2s var(--ease-in-out) infinite;
}

@keyframes app-shell-loading-pulse {
  0%,
  100% {
    transform: scale(0.78);
    opacity: 0.65;
  }

  50% {
    transform: scale(1);
    opacity: 1;
  }
}

@media (max-width: 767px) {
  .app-shell,
  .app-shell--collapsed {
    grid-template-columns: 1fr;
  }

  .app-shell__content {
    padding: var(--space-4) var(--space-3) var(--space-6);
  }
}
</style>
