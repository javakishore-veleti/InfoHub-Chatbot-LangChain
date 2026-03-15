import { Component, input, computed } from '@angular/core';
import { statusClass, statusIcon, statusLabel } from '../../utils/status.utils';

@Component({
  selector: 'app-status-badge',
  standalone: true,
  template: `
    <span [class]="badgeClass()">
      <i class="fa-solid" [class]="iconClass()"></i>
      {{ label() }}
    </span>
  `,
})
export class StatusBadgeComponent {
  status = input.required<string>();

  badgeClass = computed(() => statusClass(this.status()));
  iconClass = computed(() => statusIcon(this.status()));
  label = computed(() => statusLabel(this.status()));
}
