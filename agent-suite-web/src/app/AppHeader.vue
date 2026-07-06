<script setup lang="ts">
import { computed } from 'vue';
import { useRouter } from 'vue-router';

import { useAuthStore } from '@stores/auth';
import { useThemeStore } from '@stores/theme';
import { useToastStore } from '@stores/toast';
import AppIcon from '@components/ui/AppIcon.vue';

const props = defineProps<{ sidebarCollapsed: boolean }>();
const emit = defineEmits<{ (e: 'toggle-sidebar'): void }>();

const router = useRouter();
const auth = useAuthStore();
const theme = useThemeStore();
const toast = useToastStore();

const openAccountMenuLabel = '\u6253\u5f00\u8d26\u53f7\u83dc\u5355';
const themeLabel = computed(() =>
  theme.isDark
    ? '\u5207\u6362\u5230\u6d45\u8272\u6a21\u5f0f'
    : '\u5207\u6362\u5230\u6df1\u8272\u6a21\u5f0f',
);
const sidebarToggleLabel = computed(() =>
  props.sidebarCollapsed
    ? '\u5c55\u5f00\u667a\u80fd\u4f53\u5bfc\u822a'
    : '\u6536\u8d77\u667a\u80fd\u4f53\u5bfc\u822a',
);
const roleLabel = computed(() =>
  auth.isAdmin ? '\u7ba1\u7406\u5458\u4f53\u9a8c' : '\u7528\u6237\u4f53\u9a8c',
);

async function handleCommand(command: string): Promise<void> {
  if (command === 'profile') {
    await router.push({ name: 'profile' });
    return;
  }
  if (command === 'theme') {
    theme.toggle();
    return;
  }
  if (command === 'logout') {
    try {
      await auth.logout();
      toast.success('\u5df2\u9000\u51fa\u767b\u5f55');
      await router.push({ name: 'login' });
    } catch {
      toast.error('\u9000\u51fa\u5931\u8d25\uff0c\u8bf7\u91cd\u8bd5');
    }
  }
}
</script>

<template>
  <header class="app-header" role="banner">
    <button
      type="button"
      class="app-header__toggle"
      :aria-label="sidebarToggleLabel"
      :aria-expanded="!sidebarCollapsed"
      @click="emit('toggle-sidebar')"
    >
      <el-icon><AppIcon name="Menu" /></el-icon>
    </button>

    <div class="app-header__actions">
      <el-button
        class="app-header__theme"
        text
        :aria-label="themeLabel"
        :title="themeLabel"
        @click="theme.toggle()"
      >
        <el-icon><AppIcon :name="theme.isDark ? 'Sunny' : 'Moon'" /></el-icon>
      </el-button>
      <el-dropdown trigger="click" @command="handleCommand">
        <span
          class="app-header__user"
          tabindex="0"
          role="button"
          :aria-label="openAccountMenuLabel"
        >
          <el-avatar :size="34">{{ auth.initials }}</el-avatar>
          <span class="app-header__user-copy">
            <span class="app-header__user-name">{{ auth.displayName }}</span>
            <span class="app-header__user-role">{{ roleLabel }}</span>
          </span>
          <el-icon class="app-header__user-arrow"><AppIcon name="ArrowDown" /></el-icon>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="profile">{{ '\u4e2a\u4eba\u4fe1\u606f' }}</el-dropdown-item>
            <el-dropdown-item command="theme">{{ themeLabel }}</el-dropdown-item>
            <el-dropdown-item command="logout" divided>{{
              '\u9000\u51fa\u767b\u5f55'
            }}</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  position: sticky;
  top: 0;
  z-index: var(--z-sticky);
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--space-4);
  height: var(--layout-header-height);
  padding: var(--space-3) var(--space-6);
  background: transparent;
  border-bottom: 0;
}

/* Sidebar toggle lives in the sidebar on desktop; this is the mobile menu button only. */
.app-header__toggle {
  display: none;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
  margin-right: auto;
  width: 44px;
  height: 44px;
  border: 1px solid transparent;
  background: var(--color-surface-muted);
  border-radius: var(--radius-lg);
  color: var(--color-text-muted);
  transition:
    background-color var(--duration-fast) var(--ease-in-out),
    border-color var(--duration-fast) var(--ease-in-out),
    color var(--duration-fast) var(--ease-in-out);
}

.app-header__toggle:hover {
  background-color: var(--color-surface);
  border-color: var(--color-border);
  color: var(--color-text);
}

.app-header__actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.app-header__theme {
  min-width: 44px;
  min-height: 44px;
  border-radius: var(--radius-pill);
  color: var(--color-text-muted);
}

.app-header__user {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  min-height: 44px;
  padding: var(--space-1) var(--space-2) var(--space-1) var(--space-1);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-pill);
  background: var(--color-surface);
  box-shadow: none;
  cursor: pointer;
}

.app-header__user-copy {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.app-header__user-name {
  max-width: 132px;
  overflow: hidden;
  color: var(--color-text);
  font-size: var(--text-sm);
  font-weight: 600;
  line-height: 1.25;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.app-header__user-role {
  color: var(--color-text-subtle);
  font-size: var(--text-xs);
  line-height: 1.25;
}

.app-header__user-arrow {
  color: var(--color-text-subtle);
}

@media (max-width: 767px) {
  .app-header {
    height: 64px;
    padding: var(--space-2) var(--space-3);
  }

  .app-header__toggle {
    display: inline-flex;
  }

  .app-header__user-copy,
  .app-header__user-arrow {
    display: none;
  }
}
</style>
