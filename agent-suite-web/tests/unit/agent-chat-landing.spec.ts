import { mount } from '@vue/test-utils';
import ElementPlus from 'element-plus';
import { describe, expect, it } from 'vitest';

import AgentChatLanding from '@components/chat/AgentChatLanding.vue';

const baseProps = {
  modelValue: '',
  agentName: '法律助手',
  title: '今天想咨询什么法律问题？',
  description: '描述事实和诉求。',
  icon: 'ChatDotRound',
  tone: 'legal' as const,
  placeholder: '向法律助手提问',
  hint: 'Enter 发送',
  suggestions: [{ label: '拖欠工资怎么办', prompt: '公司拖欠工资，我该怎么处理？' }],
};

describe('AgentChatLanding', () => {
  it('fills the composer from a suggestion', async () => {
    const wrapper = mount(AgentChatLanding, {
      props: baseProps,
      global: { plugins: [ElementPlus] },
    });

    await wrapper.get('.agent-chat-landing__suggestions button').trigger('click');

    expect(wrapper.emitted('update:modelValue')).toEqual([['公司拖欠工资，我该怎么处理？']]);
  });

  it('submits a non-empty prompt with Enter', async () => {
    const wrapper = mount(AgentChatLanding, {
      props: { ...baseProps, modelValue: '测试问题' },
      global: { plugins: [ElementPlus] },
    });

    await wrapper.get('textarea').trigger('keydown', { key: 'Enter' });

    expect(wrapper.emitted('submit')).toHaveLength(1);
  });
});
