import { defineStore } from 'pinia';

export type ToastType = 'info' | 'success' | 'warning' | 'error';

export interface ToastItem {
  id: string;
  type: ToastType;
  title?: string;
  message: string;
  duration: number;
  createdAt: number;
}

export interface ToastInput {
  type?: ToastType;
  title?: string;
  message: string;
  duration?: number;
}

const DEFAULT_DURATION: Record<ToastType, number> = {
  info: 4000,
  success: 3000,
  warning: 5000,
  error: 6000,
};

function generateId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  return `toast-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

interface ToastState {
  items: ToastItem[];
}

export const useToastStore = defineStore('toast', {
  state: (): ToastState => ({
    items: [],
  }),
  actions: {
    push(input: ToastInput | string): string {
      const payload: ToastInput = typeof input === 'string' ? { message: input } : input;
      const type = payload.type ?? 'info';
      const item: ToastItem = {
        id: generateId(),
        type,
        title: payload.title,
        message: payload.message,
        duration: payload.duration ?? DEFAULT_DURATION[type],
        createdAt: Date.now(),
      };
      this.items.push(item);
      if (item.duration > 0) {
        setTimeout(() => this.dismiss(item.id), item.duration);
      }
      return item.id;
    },
    info(message: string, title?: string): string {
      return this.push({ type: 'info', message, title });
    },
    success(message: string, title?: string): string {
      return this.push({ type: 'success', message, title });
    },
    warning(message: string, title?: string): string {
      return this.push({ type: 'warning', message, title });
    },
    error(message: string, title?: string): string {
      return this.push({ type: 'error', message, title });
    },
    dismiss(id: string): void {
      const index = this.items.findIndex((item) => item.id === id);
      if (index >= 0) this.items.splice(index, 1);
    },
    clear(): void {
      this.items.splice(0, this.items.length);
    },
  },
});
