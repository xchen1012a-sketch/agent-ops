import { mount } from '@vue/test-utils';
import ElementPlus from 'element-plus';
import { describe, expect, it } from 'vitest';

import AsyncState from '@components/ui/AsyncState.vue';
import RetryAction from '@components/ui/RetryAction.vue';
import { API_ERROR_CODES } from '@/types/api';
import {
  createErrorState,
  createLoadingState,
  createSuccessState,
  mapRequestError,
} from '@lib/request-state';

describe('RetryAction', () => {
  it('renders error details and emits retry for retryable errors', async () => {
    const wrapper = mount(RetryAction, {
      props: {
        error: mapRequestError({
          error_code: API_ERROR_CODES.RATE_LIMITED,
          message: 'too many requests',
          retry_after_seconds: 10,
          trace_id: 'trace-1',
        }),
      },
      global: { plugins: [ElementPlus] },
    });

    expect(wrapper.text()).toContain('慢一点');
    expect(wrapper.text()).toContain('too many requests');
    expect(wrapper.text()).toContain('10 秒后重试');
    expect(wrapper.text()).toContain('trace-1');

    await wrapper.find('button').trigger('click');
    expect(wrapper.emitted('retry')).toHaveLength(1);
  });

  it('hides retry button for non-retryable errors', () => {
    const wrapper = mount(RetryAction, {
      props: {
        error: mapRequestError({ error_code: API_ERROR_CODES.AUTH_FORBIDDEN }),
      },
      global: { plugins: [ElementPlus] },
    });

    expect(wrapper.find('button').exists()).toBe(false);
  });
});

describe('AsyncState', () => {
  it('renders loading state', () => {
    const wrapper = mount(AsyncState, {
      props: { state: createLoadingState(), loadingMessage: '正在加载列表' },
      global: { plugins: [ElementPlus] },
    });

    expect(wrapper.text()).toContain('正在加载列表');
  });

  it('renders retry action for error state', async () => {
    const wrapper = mount(AsyncState, {
      props: {
        state: createErrorState({ error_code: 'NETWORK_ERROR' }),
      },
      global: { plugins: [ElementPlus] },
    });

    expect(wrapper.text()).toContain('网络异常');
    await wrapper.find('button').trigger('click');
    expect(wrapper.emitted('retry')).toHaveLength(1);
  });

  it('renders empty state and emits empty action', async () => {
    const wrapper = mount(AsyncState, {
      props: {
        state: createSuccessState([]),
        emptyTitle: '没有报告',
        emptyDescription: '当前筛选下没有报告。',
        emptyActionText: '新建报告',
      },
      global: { plugins: [ElementPlus] },
    });

    expect(wrapper.text()).toContain('没有报告');
    expect(wrapper.text()).toContain('当前筛选下没有报告。');
    await wrapper.find('button').trigger('click');
    expect(wrapper.emitted('empty-action')).toHaveLength(1);
  });

  it('renders default slot for success state', () => {
    const wrapper = mount(AsyncState, {
      props: { state: createSuccessState({ title: '报告详情' }) },
      slots: {
        default: '<template #default="{ data }"><article>{{ data.title }}</article></template>',
      },
      global: { plugins: [ElementPlus] },
    });

    expect(wrapper.text()).toContain('报告详情');
  });
});
