import { describe, expect, it } from 'vitest';

import { createConversationTitle } from '@/lib/conversation-title';

describe('createConversationTitle', () => {
  it('extracts a concise title from the first question', () => {
    expect(createConversationTitle('请帮我看看合同违约责任是否合理？')).toBe(
      '看看合同违约责任是否合理',
    );
  });

  it('normalizes markdown, links, whitespace, and long content', () => {
    expect(
      createConversationTitle(
        '## 帮我 分析一下 https://example.com 本周销售额最高的商品有哪些，以及为什么增长',
      ),
    ).toBe('分析一下 本周销售额最高的商品有哪些，以及为什么…');
  });

  it('falls back when no usable content is available', () => {
    expect(createConversationTitle('   ', '新的法律咨询')).toBe('新的法律咨询');
  });
});
