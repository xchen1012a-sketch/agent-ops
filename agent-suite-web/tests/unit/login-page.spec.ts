import { flushPromises, mount } from '@vue/test-utils';
import ElementPlus from 'element-plus';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import LoginPage from '@views/auth/LoginPage.vue';

const authLogin = vi.fn();
const toastSuccess = vi.fn();
const toastError = vi.fn();
const routerPush = vi.fn();

vi.mock('@stores/auth', () => ({
  useAuthStore: () => ({
    login: authLogin,
  }),
}));

vi.mock('@stores/toast', () => ({
  useToastStore: () => ({
    success: toastSuccess,
    error: toastError,
  }),
}));

vi.mock('vue-router', () => ({
  useRoute: () => ({ query: {} }),
  useRouter: () => ({ push: routerPush }),
}));

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    authLogin.mockResolvedValue({
      user_id: 'u-1',
      public_id: 'user-public-1',
      email: 'admin@example.com',
      display_name: 'Admin',
      role: 'admin',
      status: 'active',
    });
  });

  it('submits credentials through auth store when the login form is submitted', async () => {
    const wrapper = mount(LoginPage, {
      global: {
        plugins: [ElementPlus],
      },
    });

    await wrapper.find('input[type="email"]').setValue(' admin@example.com ');
    await wrapper.find('input[type="password"]').setValue('Admin123456');
    await wrapper.find('form').trigger('submit');
    await flushPromises();

    expect(authLogin).toHaveBeenCalledWith({
      email: 'admin@example.com',
      password: 'Admin123456',
    });
    expect(toastSuccess).toHaveBeenCalledWith('登录成功');
    expect(routerPush).toHaveBeenCalledWith('/legal');
  });
});
