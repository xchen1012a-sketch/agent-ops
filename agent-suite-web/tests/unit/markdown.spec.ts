import { describe, expect, it } from 'vitest';

import { renderMarkdown } from '@lib/markdown';

describe('renderMarkdown', () => {
  it('returns empty string for null input', () => {
    expect(renderMarkdown(null)).toBe('');
    expect(renderMarkdown(undefined)).toBe('');
    expect(renderMarkdown('')).toBe('');
  });

  it('renders basic markdown to html', () => {
    const html = renderMarkdown('# Title\n\nparagraph text');
    expect(html).toContain('<h1>Title</h1>');
    expect(html).toContain('<p>paragraph text</p>');
  });

  it('strips script tags', () => {
    const html = renderMarkdown('<script>alert(1)</script>');
    expect(html).not.toContain('<script>');
    expect(html).not.toContain('alert(1)');
  });

  it('strips javascript: urls', () => {
    const html = renderMarkdown('<a href="javascript:alert(1)">x</a>');
    expect(html).not.toContain('javascript:');
  });

  it('strips iframe tags', () => {
    const html = renderMarkdown('<iframe src="https://evil.com"></iframe>');
    expect(html).not.toContain('<iframe');
  });

  it('forces external links to open in new tab with rel attributes', () => {
    const html = renderMarkdown('[example](https://example.com)');
    expect(html).toContain('target="_blank"');
    expect(html).toContain('rel="noopener noreferrer"');
  });

  it('preserves citation blockquote', () => {
    const html = renderMarkdown('> 引用原文');
    expect(html).toContain('<blockquote');
    expect(html).toContain('引用原文');
  });

  it('allows tables', () => {
    const html = renderMarkdown('| a | b |\n| --- | --- |\n| 1 | 2 |');
    expect(html).toContain('<table>');
    expect(html).toContain('<th>a</th>');
  });
});
