import { Injectable, signal } from '@angular/core';

export interface ConfirmOptions {
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: 'danger' | 'primary';
}

export interface ConfirmState extends ConfirmOptions {
  resolve: (result: boolean) => void;
}

@Injectable({ providedIn: 'root' })
export class ConfirmService {
  readonly state = signal<ConfirmState | null>(null);

  confirm(options: ConfirmOptions): Promise<boolean> {
    return new Promise<boolean>(resolve => {
      this.state.set({ ...options, resolve });
    });
  }

  close(result: boolean): void {
    const current = this.state();
    if (current) {
      current.resolve(result);
      this.state.set(null);
    }
  }
}
