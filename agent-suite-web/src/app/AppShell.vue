<script setup lang="ts">
import { computed, ref } from 'vue';
import { useRoute } from 'vue-router';

import AppHeader from './AppHeader.vue';
import AppSidebar from './AppSidebar.vue';
import AppBreadcrumb from './AppBreadcrumb.vue';
import ErrorBoundary from './ErrorBoundary.vue';
import GlobalToast from './GlobalToast.vue';

const route = useRoute();
const sidebarCollapsed = ref(false);

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
      <AppBreadcrumb />
      <main class="app-shell__content" role="main">
        <ErrorBoundary>
          <RouterView v-slot="{ Component }">
            <Suspense>
              <component :is="Component" />
              <template #fallback>
                <div class="app-shell__loading" role="status" aria-live="polite">
                  <el-icon class="is-loading">
                    <Loading />
                  </el-icon>
                  <span>页面加载中…</span>
                </div>
              </template>
            </Suspense>
          </RouterView>
        </ErrorBoundary>
      </main>
    </div>
    <GlobalToast />
  </div>
</template>

<style scoped>
.app-shell {
  display: grid;
  grid-template-columns: var(--layout-sidebar-width) 1fr;
  min-height: 100vh;
  background-color: var(--color-bg);
  transition: grid-template-columns var(--duration-normal) var(--ease-in-out);
}

.app-shell--collapsed {
  grid-template-columns: var(--layout-sidebar-collapsed-width) 1fr;
}

.app-shell__main {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.app-shell__content {
  flex: 1 1 auto;
  padding: var(--space-6);
  background-color: var(--color-bg);
}

.app-shell__loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-12);
  color: var(--color-text-muted);
}

@media (max-width: 767px) {
  .app-shell,
  .app-shell--collapsed {
    grid-template-columns: 1fr;
  }

  .app-shell__content {
    padding: var(--space-3);
  }
}
</style>
