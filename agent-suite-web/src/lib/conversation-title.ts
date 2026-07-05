const DEFAULT_TITLE_MAX_LENGTH = 24;

const LEADING_FILLERS = [
  '请问',
  '帮我',
  '帮忙',
  '我想',
  '想问',
  '咨询一下',
  '请帮我',
  '能不能',
  '可以',
  '请',
];

export function createConversationTitle(
  content: string | null | undefined,
  fallback = '新的对话',
): string {
  const normalized = normalizeTitleSource(content);
  if (!normalized) return fallback;

  const withoutFiller = trimLeadingFiller(normalized);
  const title = truncateByCharacters(withoutFiller || normalized, DEFAULT_TITLE_MAX_LENGTH);
  return title || fallback;
}

function normalizeTitleSource(content: string | null | undefined): string {
  return String(content ?? '')
    .replace(/[#*_`>~|[\](){}]/g, '')
    .replace(/https?:\/\/\S+/gi, '')
    .replace(/\s+/g, ' ')
    .replace(/^[\s"'“”‘’.,，。:：;；!?！？、-]+/, '')
    .replace(/[\s"'“”‘’.,，。:：;；!?！？、-]+$/g, '')
    .trim();
}

function trimLeadingFiller(value: string): string {
  let title = value;
  for (const filler of LEADING_FILLERS) {
    if (title.startsWith(filler)) {
      title = title.slice(filler.length).trim();
      break;
    }
  }
  return title.replace(/^[，。:：;；!?！？、\s]+/, '').trim();
}

function truncateByCharacters(value: string, maxLength: number): string {
  const chars = Array.from(value);
  if (chars.length <= maxLength) return value;
  return `${chars.slice(0, maxLength).join('').trimEnd()}…`;
}
