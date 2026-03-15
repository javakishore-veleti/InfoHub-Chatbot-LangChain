import { Injectable, signal } from '@angular/core';

export interface Toast {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration: number;
  createdAt: number;
}

@Injectable({ providedIn: 'root' })
export class ToastService {
  readonly toasts = signal<Toast[]>([]);
  private timers = new Map<string, ReturnType<typeof setTimeout>>();

  success(title: string, message?: string): void {
    this.show({ type: 'success', title, message, duration: 5000 });
  }

  error(title: string, message?: string): void {
    this.show({ type: 'error', title, message, duration: 0 });
  }

  warning(title: string, message?: string): void {
    this.show({ type: 'warning', title, message, duration: 6000 });
  }

  info(title: string, message?: string): void {
    this.show({ type: 'info', title, message, duration: 5000 });
  }

  dismiss(id: string): void {
    this.toasts.update(list => list.filter(t => t.id !== id));
    const timer = this.timers.get(id);
    if (timer) {
      clearTimeout(timer);
      this.timers.delete(id);
    }
  }

  private show(opts: Omit<Toast, 'id' | 'createdAt'>): void {
    const id = crypto.randomUUID();
    const toast: Toast = { ...opts, id, createdAt: Date.now() };
    this.toasts.update(list => [...list, toast]);

    if (opts.duration > 0) {
      const timer = setTimeout(() => this.dismiss(id), opts.duration);
      this.timers.set(id, timer);
    }
  }
}
