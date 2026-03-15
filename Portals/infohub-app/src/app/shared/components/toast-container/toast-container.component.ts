import { Component, inject } from '@angular/core';
import { ToastService } from '../../services/toast.service';

@Component({
  selector: 'app-toast-container',
  standalone: true,
  template: `
    <div class="ih-toast-container">
      @for (toast of toastService.toasts(); track toast.id) {
        <div class="ih-toast ih-toast--{{ toast.type }}">
          <div class="ih-toast__icon">
            @switch (toast.type) {
              @case ('success') { <i class="fa-solid fa-circle-check"></i> }
              @case ('error') { <i class="fa-solid fa-circle-xmark"></i> }
              @case ('warning') { <i class="fa-solid fa-triangle-exclamation"></i> }
              @case ('info') { <i class="fa-solid fa-circle-info"></i> }
            }
          </div>
          <div class="ih-toast__body">
            <div class="ih-toast__title">{{ toast.title }}</div>
            @if (toast.message) {
              <div class="ih-toast__message">{{ toast.message }}</div>
            }
          </div>
          <button class="ih-toast__close" (click)="toastService.dismiss(toast.id)" aria-label="Dismiss">
            <i class="fa-solid fa-xmark"></i>
          </button>
          @if (toast.duration > 0) {
            <div class="ih-toast__progress" [style.animation-duration.ms]="toast.duration"></div>
          }
        </div>
      }
    </div>
  `,
  styles: `
    .ih-toast-container {
      position: fixed;
      top: 68px;
      right: var(--ih-space-lg);
      z-index: 1060;
      width: 380px;
      display: flex;
      flex-direction: column;
      gap: var(--ih-space-sm);
    }

    .ih-toast {
      background: var(--ih-surface);
      border: 1px solid var(--ih-border);
      border-radius: var(--ih-radius-md);
      box-shadow: var(--ih-elevation-3);
      display: flex;
      align-items: flex-start;
      gap: 12px;
      padding: 14px 16px;
      position: relative;
      overflow: hidden;
      animation: ih-toast-in 0.25s ease-out;
    }

    @keyframes ih-toast-in {
      from { opacity: 0; transform: translateX(20px); }
      to   { opacity: 1; transform: translateX(0); }
    }

    .ih-toast--success { border-left: 3px solid var(--ih-success-text); }
    .ih-toast--error   { border-left: 3px solid var(--ih-danger-text); }
    .ih-toast--warning { border-left: 3px solid var(--ih-warn-text); }
    .ih-toast--info    { border-left: 3px solid var(--ih-info-text); }

    .ih-toast__icon {
      font-size: 1.1rem;
      flex-shrink: 0;
      margin-top: 1px;
    }
    .ih-toast--success .ih-toast__icon { color: var(--ih-success-text); }
    .ih-toast--error   .ih-toast__icon { color: var(--ih-danger-text); }
    .ih-toast--warning .ih-toast__icon { color: var(--ih-warn-text); }
    .ih-toast--info    .ih-toast__icon { color: var(--ih-info-text); }

    .ih-toast__body { flex: 1; min-width: 0; }
    .ih-toast__title { font-weight: 600; font-size: var(--ih-font-base); color: var(--ih-text); }
    .ih-toast__message { font-size: var(--ih-font-sm); color: var(--ih-muted); margin-top: 2px; }

    .ih-toast__close {
      background: none;
      border: none;
      color: var(--ih-muted);
      cursor: pointer;
      padding: 2px;
      font-size: var(--ih-font-sm);
      flex-shrink: 0;
    }
    .ih-toast__close:hover { color: var(--ih-text); }

    .ih-toast__progress {
      position: absolute;
      bottom: 0;
      left: 0;
      height: 2px;
      background: var(--ih-brand);
      animation: ih-toast-progress linear forwards;
      width: 100%;
    }
    @keyframes ih-toast-progress {
      from { width: 100%; }
      to   { width: 0%; }
    }

    @media (max-width: 575.98px) {
      .ih-toast-container {
        width: calc(100vw - 32px);
        right: 16px;
      }
    }
  `,
})
export class ToastContainerComponent {
  protected readonly toastService = inject(ToastService);
}
