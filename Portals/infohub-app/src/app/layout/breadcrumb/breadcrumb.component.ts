import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { BreadcrumbService } from '../../shared/services/breadcrumb.service';

@Component({
  selector: 'app-breadcrumb',
  standalone: true,
  imports: [RouterLink],
  template: `
    <nav class="ih-breadcrumb" aria-label="Breadcrumb">
      <ol>
        @for (seg of breadcrumbs.segments(); track seg.label; let last = $last) {
          <li [class.ih-breadcrumb__current]="last">
            @if (last) {
              @if (seg.icon) {
                <i class="fa-solid {{ seg.icon }}"></i>
              }
              <span>{{ seg.label }}</span>
            } @else {
              @if (seg.path) {
                <a [routerLink]="seg.path">{{ seg.label }}</a>
              } @else {
                <span class="ih-breadcrumb__parent">{{ seg.label }}</span>
              }
              <i class="fa-solid fa-chevron-right ih-breadcrumb__sep"></i>
            }
          </li>
        }
      </ol>
    </nav>
  `,
  styles: `
    .ih-breadcrumb ol {
      list-style: none;
      display: flex;
      align-items: center;
      gap: 6px;
      margin: 0;
      padding: 0;
    }
    .ih-breadcrumb li {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: var(--ih-font-base);
      color: var(--ih-muted);
    }
    .ih-breadcrumb__current {
      color: var(--ih-text) !important;
      font-weight: 600;
    }
    .ih-breadcrumb a {
      color: var(--ih-muted);
      text-decoration: none;
    }
    .ih-breadcrumb a:hover {
      color: var(--ih-brand);
    }
    .ih-breadcrumb__sep {
      font-size: 0.55rem;
      color: var(--ih-muted);
      opacity: 0.6;
    }
    .ih-breadcrumb__parent {
      color: var(--ih-muted);
    }
  `,
})
export class BreadcrumbComponent {
  protected readonly breadcrumbs = inject(BreadcrumbService);
}
