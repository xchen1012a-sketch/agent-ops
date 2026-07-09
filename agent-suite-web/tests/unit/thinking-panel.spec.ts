import { mount } from '@vue/test-utils';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import ThinkingPanel from '@components/chat/ThinkingPanel.vue';

const baseProps = {
  thinking: '正在拆解问题',
  phase: 'thinking' as const,
  elapsedSeconds: 3,
  durationMs: null as number | null,
  expanded: true,
};

describe('ThinkingPanel', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('renders nothing when there is no thinking content', () => {
    const wrapper = mount(ThinkingPanel, { props: { ...baseProps, thinking: '   ' } });
    expect(wrapper.find('.thinking-panel').exists()).toBe(false);
  });

  it('shows the shimmering "Thinking" label with animated dots while thinking', () => {
    const wrapper = mount(ThinkingPanel, { props: baseProps });
    expect(wrapper.find('.thinking-panel__label').text()).toBe('Thinking');
    expect(wrapper.find('.thinking-panel__dots').exists()).toBe(true);
  });

  it('shows the frozen "已思考 X 秒" label after thinking ends', () => {
    const wrapper = mount(ThinkingPanel, {
      props: { ...baseProps, phase: 'answering', durationMs: 2000 },
    });
    expect(wrapper.find('.thinking-panel__label').text()).toBe('已思考 2 秒');
  });

  it('emits toggle when the header is clicked', async () => {
    const wrapper = mount(ThinkingPanel, { props: baseProps });
    await wrapper.find('.thinking-panel__header').trigger('click');
    expect(wrapper.emitted('toggle')).toHaveLength(1);
  });

  it('typewrites the thinking text into the expanded body', async () => {
    const wrapper = mount(ThinkingPanel, { props: baseProps });
    await vi.advanceTimersByTimeAsync(500);
    expect(wrapper.find('.thinking-panel__text').text()).toBe('正在拆解问题');
  });

  it('hides the body when collapsed', () => {
    const wrapper = mount(ThinkingPanel, { props: { ...baseProps, expanded: false } });
    const body = wrapper.find('.thinking-panel__body');
    expect(body.attributes('style')).toContain('display: none');
  });
});
