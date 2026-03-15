import { Component, inject } from '@angular/core';
import { ConfirmService } from '../../services/confirm.service';

@Component({
  selector: 'app-confirm-dialog',
  standalone: true,
  template: `
    @if (confirmService.state(); as state) {
      <div class="ih-confirm-backdrop" (click)="confirmService.close(false)"></div>
      <div class="ih-confirm">
        <div class="ih-confirm__header">
          <h3 class="ih-confirm__title">{{ state.title }}</h3>
        </div>
        <div class="ih-confirm__body">
          <p>{{ state.message }}</p>
        </div>
        <div class="ih-confirm__footer">
          <button class="btn btn-outline-secondary" (click)="confirmService.close(false)">
            {{ state.cancelLabel || 'Cancel' }}
          </button>
          <button class="btn"
                  [class.btn-primary]="state.variant !== 'danger'"
                  [class.btn-danger]="state.variant === 'danger'"
                  (click)="confirmService.close(true)">
            {{ state.confirmLabel || 'Confirm' }}
          </button>
        </div>
      </div>
    }
  `,
  styles: `
    .ih-confirm-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.45);
      z-index: 1070;
    }

    .ih-confirm {
      position: fixed;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      z-index: 1080;
      background: var(--ih-surface);
      border: 1px solid var(--ih-border);
      border-radius: var(--ih-radius-lg);
      box-shadow: var(--ih-elevation-4);
      width: min(440px, calc(100vw - 32px));
      animation: ih-confirm-in 0.2s ease-out;
    }

    @keyframes ih-confirm-in {
      from { opacity: 0; transform: translate(-50%, -48%); }
      to   { opacity: 1; transform: translate(-50%, -50%); }
    }

    .ih-confirm__header {
      padding: 20px 24px 0;
    }

    .ih-confirm__title {
      font-size: var(--ih-font-lg);
      font-weight: 700;
      margin: 0;
    }

    .ih-confirm__body {
      padding: 12px 24px 20px;
      color: var(--ih-muted);
      font-size: var(--ih-font-base);
    }

    .ih-confirm__body p {
      margin: 0;
    }

    .ih-confirm__footer {
      display: flex;
      justify-content: flex-end;
      gap: var(--ih-space-sm);
      padding: 0 24px 20px;
    }
  `,
})
export class ConfirmDialogComponent {
  protected readonly confirmService = inject(ConfirmService);
}
