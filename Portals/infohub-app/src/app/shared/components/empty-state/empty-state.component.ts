import { Component, input } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-empty-state',
  standalone: true,
  imports: [RouterLink],
  template: `
    <div class="ih-empty">
      <i class="fa-solid {{ icon() }} ih-empty__icon"></i>
      <h4 class="ih-empty__title">{{ title() }}</h4>
      @if (description()) {
        <p class="ih-empty__desc">{{ description() }}</p>
      }
      @if (actionLabel() && actionLink()) {
        <a class="btn btn-primary btn-sm" [routerLink]="actionLink()">
          <i class="fa-solid fa-plus me-1"></i>{{ actionLabel() }}
        </a>
      }
    </div>
  `,
  styles: `
    .ih-empty {
      text-align: center;
      padding: var(--ih-space-2xl) var(--ih-space-lg);
      border: 1px dashed var(--ih-border);
      border-radius: var(--ih-radius-lg);
      background: color-mix(in srgb, var(--ih-soft) 50%, var(--ih-surface));
    }
    .ih-empty__icon {
      font-size: 2.5rem;
      color: var(--ih-muted);
      opacity: 0.5;
      margin-bottom: var(--ih-space-md);
      display: block;
    }
    .ih-empty__title {
      font-size: var(--ih-font-md);
      font-weight: 600;
      color: var(--ih-text);
      margin: 0 0 var(--ih-space-sm);
    }
    .ih-empty__desc {
      color: var(--ih-muted);
      font-size: var(--ih-font-base);
      margin: 0 0 var(--ih-space-md);
    }
  `,
})
export class EmptyStateComponent {
  icon = input('fa-folder-open');
  title = input('No data found');
  description = input('');
  actionLabel = input('');
  actionLink = input('');
}
