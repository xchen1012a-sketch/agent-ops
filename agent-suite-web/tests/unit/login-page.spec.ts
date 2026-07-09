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

  it('opens login dialog and submits credentials through auth store', async () => {
    const wrapper = mount(LoginPage, {
      global: {
        plugins: [ElementPlus],
        stubs: {
          teleport: true,
          transition: false,
        },
      },
    });

    expect(wrapper.find('input[type="email"]').exists()).toBe(false);

    await wrapper.find('.login-top-bar__login').trigger('click');
    await flushPromises();

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
