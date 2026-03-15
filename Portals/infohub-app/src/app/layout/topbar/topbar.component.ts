import { Component, inject, output, signal } from '@angular/core';
import { BreadcrumbComponent } from '../breadcrumb/breadcrumb.component';
import { WorkflowApiService } from '../../services/workflow-api.service';
import { ToastService } from '../../shared/services/toast.service';

@Component({
  selector: 'app-topbar',
  standalone: true,
  imports: [BreadcrumbComponent],
  templateUrl: './topbar.component.html',
  styleUrl: './topbar.component.css',
})
export class TopbarComponent {
  toggleSidebar = output<void>();
  toggleCollapse = output<void>();

  private readonly api = inject(WorkflowApiService);
  private readonly toast = inject(ToastService);

  readonly apiOnline = signal(true);
  readonly theme = signal<'light' | 'dark'>(this.getStoredTheme());
  private wasOnline = true;
  private healthInterval: ReturnType<typeof setInterval> | undefined;

  constructor() {
    this.applyTheme(this.theme());
    this.checkHealth();
    this.healthInterval = setInterval(() => this.checkHealth(), 30_000);
  }

  toggleTheme(): void {
    const next = this.theme() === 'dark' ? 'light' : 'dark';
    this.theme.set(next);
    this.applyTheme(next);
    localStorage.setItem('infohub.theme', next);
  }

  isDark(): boolean {
    return this.theme() === 'dark';
  }

  private checkHealth(): void {
    this.api.checkApiHealth().subscribe({
      next: () => {
        this.apiOnline.set(true);
        if (!this.wasOnline) {
          this.toast.success('API Connected', 'Backend is now available.');
        }
        this.wasOnline = true;
      },
      error: () => {
        this.apiOnline.set(false);
        if (this.wasOnline) {
          this.toast.warning('API Disconnected', 'Some features may be unavailable.');
        }
        this.wasOnline = false;
      },
    });
  }

  private applyTheme(theme: 'light' | 'dark'): void {
    document.documentElement.setAttribute('data-theme', theme);
  }

  private getStoredTheme(): 'light' | 'dark' {
    const stored = localStorage.getItem('infohub.theme');
    if (stored === 'dark' || stored === 'light') return stored;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
}
