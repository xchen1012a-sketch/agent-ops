import { createPinia, setActivePinia } from 'pinia';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useToastStore } from '@stores/toast';

describe('toast store', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.useFakeTimers();
  });

  it('pushes a toast with default type info', () => {
    const toast = useToastStore();
    const id = toast.push('hello');
    expect(toast.items).toHaveLength(1);
    expect(toast.items[0]?.id).toBe(id);
    expect(toast.items[0]?.type).toBe('info');
    expect(toast.items[0]?.message).toBe('hello');
  });

  it('auto-dismisses after duration', () => {
    const toast = useToastStore();
    toast.push({ message: 'temp', duration: 1000 });
    expect(toast.items).toHaveLength(1);
    vi.advanceTimersByTime(1100);
    expect(toast.items).toHaveLength(0);
  });

  it('clears all toasts', () => {
    const toast = useToastStore();
    toast.success('a');
    toast.error('b');
    toast.clear();
    expect(toast.items).toHaveLength(0);
  });

  it('dismisses by id', () => {
    const toast = useToastStore();
    const id = toast.info('keep');
    toast.info('drop');
    toast.dismiss(id);
    expect(toast.items).toHaveLength(1);
    expect(toast.items[0]?.message).toBe('drop');
  });
});
