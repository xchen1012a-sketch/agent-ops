import { flushPromises, mount } from '@vue/test-utils';
import ElementPlus from 'element-plus';
import { describe, expect, it, vi } from 'vitest';

import ChatComposer from '@components/chat/ChatComposer.vue';

const baseProps = {
  modelValue: '',
  tone: 'legal' as const,
  placeholder: '向助手提问',
  hint: 'Enter 发送，Shift + Enter 换行',
  inputLabel: '向助手提问',
};

function mountComposer(props = {}) {
  return mount(ChatComposer, {
    props: {
      ...baseProps,
      ...props,
    },
    global: { plugins: [ElementPlus] },
  });
}

function clipboardFileItem(file: Partial<File>) {
  return {
    kind: 'file',
    getAsFile: () => file,
  };
}

async function dispatchPaste(wrapper: ReturnType<typeof mountComposer>, items: unknown[]) {
  const event = new Event('paste', { bubbles: true, cancelable: true });
  const preventDefault = vi.fn();
  Object.defineProperty(event, 'clipboardData', { value: { items } });
  Object.defineProperty(event, 'preventDefault', { value: preventDefault });

  wrapper.get('.chat-composer__input').element.dispatchEvent(event);
  await flushPromises();

  return preventDefault;
}

describe('ChatComposer', () => {
  it('submits a non-empty prompt with Enter', async () => {
    const wrapper = mountComposer({ modelValue: '测试问题' });

    await wrapper.get('textarea').trigger('keydown', { key: 'Enter' });

    expect(wrapper.emitted('submit')).toHaveLength(1);
  });

  it('keeps Shift Enter for newline input', async () => {
    const wrapper = mountComposer({ modelValue: '测试问题' });

    await wrapper.get('textarea').trigger('keydown', { key: 'Enter', shiftKey: true });

    expect(wrapper.emitted('submit')).toBeUndefined();
  });

  it('appends pasted text file content to the prompt', async () => {
    const file = {
      name: 'case-note.txt',
      type: 'text/plain',
      size: 18,
      text: vi.fn().mockResolvedValue('这里是文件内容'),
    } as unknown as File;
    const wrapper = mountComposer({ modelValue: '已有问题' });

    const preventDefault = await dispatchPaste(wrapper, [clipboardFileItem(file)]);

    expect(preventDefault).toHaveBeenCalled();
    expect(wrapper.emitted('update:modelValue')?.at(-1)).toEqual([
      '已有问题\n\n[文件：case-note.txt]\n这里是文件内容',
    ]);
    expect(wrapper.text()).toContain('已读入');
  });

  it('rejects pasted images with a soft OCR notice', async () => {
    const image = {
      name: 'screenshot.png',
      type: 'image/png',
      size: 1024,
    } as unknown as File;
    const wrapper = mountComposer({ modelValue: '已有问题' });

    const preventDefault = await dispatchPaste(wrapper, [clipboardFileItem(image)]);

    expect(preventDefault).toHaveBeenCalled();
    expect(wrapper.emitted('update:modelValue')).toBeUndefined();
    expect(wrapper.text()).toContain('还没有接入 OCR');
  });
});
