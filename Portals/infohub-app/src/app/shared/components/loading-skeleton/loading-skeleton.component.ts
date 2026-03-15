import { Component, input } from '@angular/core';

@Component({
  selector: 'app-loading-skeleton',
  standalone: true,
  template: `
    @for (i of items(); track i) {
      @switch (variant()) {
        @case ('card') {
          <div class="ih-skel ih-skel--card"></div>
        }
        @case ('table-row') {
          <div class="ih-skel ih-skel--row"></div>
        }
        @case ('text') {
          <div class="ih-skel ih-skel--text" [style.width]="randomWidth(i)"></div>
        }
      }
    }
  `,
  styles: `
    :host { display: block; }
    .ih-skel {
      background: linear-gradient(90deg, var(--ih-soft) 25%, var(--ih-surface-hover) 50%, var(--ih-soft) 75%);
      background-size: 800px 100%;
      animation: ih-shimmer 1.6s infinite linear;
      border-radius: var(--ih-radius-sm);
      margin-bottom: var(--ih-space-sm);
    }
    .ih-skel--card  { height: 120px; border-radius: var(--ih-radius-lg); margin-bottom: var(--ih-space-md); }
    .ih-skel--row   { height: 48px; }
    .ih-skel--text  { height: 14px; margin-bottom: 10px; }

    @keyframes ih-shimmer {
      0%   { background-position: -400px 0; }
      100% { background-position:  400px 0; }
    }
  `,
})
export class LoadingSkeletonComponent {
  variant = input<'card' | 'table-row' | 'text'>('card');
  count = input(3);

  items(): number[] {
    return Array.from({ length: this.count() }, (_, i) => i);
  }

  randomWidth(index: number): string {
    const widths = ['100%', '85%', '92%', '78%', '95%'];
    return widths[index % widths.length];
  }
}
