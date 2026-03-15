import { Component, input, output, signal } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [RouterLink, RouterLinkActive],
  templateUrl: './sidebar.component.html',
  styleUrl: './sidebar.component.css',
})
export class SidebarComponent {
  collapsed = input(false);
  mobileOpen = input(false);
  mobileClose = output<void>();

  readonly openSections = signal<Set<string>>(new Set(['ingest']));

  isSectionOpen(name: string): boolean {
    return this.openSections().has(name);
  }

  toggleSection(name: string): void {
    this.openSections.update(set => {
      const next = new Set(set);
      if (next.has(name)) {
        next.delete(name);
      } else {
        next.add(name);
      }
      return next;
    });
  }

  onBackdropClick(): void {
    this.mobileClose.emit();
  }
}
