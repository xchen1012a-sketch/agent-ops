<script setup lang="ts">
import { computed } from 'vue';
import { useRouter } from 'vue-router';

import { useAuthStore } from '@stores/auth';
import { useThemeStore } from '@stores/theme';
import { useToastStore } from '@stores/toast';

defineProps<{ sidebarCollapsed: boolean }>();
const emit = defineEmits<{ (e: 'toggle-sidebar'): void }>();

const router = useRouter();
const auth = useAuthStore();
const theme = useThemeStore();
const toast = useToastStore();

const themeLabel = computed(() => (theme.isDark ? '切换到浅色' : '切换到深色'));

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
      toast.success('已退出登录');
      await router.push({ name: 'login' });
    } catch (error) {
      toast.error('登出失败，请重试');
      console.error('[logout]', error);
    }
  }
}
</script>

<template>
  <header class="app-header" role="banner">
    <button
      type="button"
      class="app-header__toggle"
      :aria-label="sidebarCollapsed ? '展开侧边栏' : '收起侧边栏'"
      :aria-expanded="!sidebarCollapsed"
      @click="emit('toggle-sidebar')"
    >
      <el-icon><Menu /></el-icon>
    </button>
    <div class="app-header__brand">
      <span class="app-header__brand-title">企业智能体平台</span>
    </div>
    <div class="app-header__actions">
      <el-button text :aria-label="themeLabel" :title="themeLabel" @click="theme.toggle()">
        <el-icon><component :is="theme.isDark ? 'Sunny' : 'Moon'" /></el-icon>
      </el-button>
      <el-dropdown trigger="click" @command="handleCommand">
        <span class="app-header__user" tabindex="0">
          <el-avatar :size="32">{{ auth.initials }}</el-avatar>
          <span class="app-header__user-name">{{ auth.displayName }}</span>
          <el-icon><ArrowDown /></el-icon>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="profile"> 个人信息 </el-dropdown-item>
            <el-dropdown-item command="theme">
              {{ theme.isDark ? '切换到浅色' : '切换到深色' }}
            </el-dropdown-item>
            <el-dropdown-item command="logout" divided> 退出登录 </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  height: var(--layout-header-height);
  padding: 0 var(--space-4);
  background-color: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}

.app-header__toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border: none;
  background-color: transparent;
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
  transition:
    background-color var(--duration-fast) var(--ease-in-out),
    color var(--duration-fast) var(--ease-in-out);
}

.app-header__toggle:hover {
  background-color: var(--color-surface-muted);
  color: var(--color-text);
}

.app-header__brand {
  flex: 1 1 auto;
  min-width: 0;
}

.app-header__brand-title {
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--color-text);
}

.app-header__actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.app-header__user {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-md);
  cursor: pointer;
}

.app-header__user-name {
  font-size: var(--text-sm);
  color: var(--color-text);
}

@media (max-width: 767px) {
  .app-header__user-name {
    display: none;
  }
}
</style>
