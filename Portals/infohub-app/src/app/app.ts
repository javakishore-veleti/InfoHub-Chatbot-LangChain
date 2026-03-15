import { NgClass } from '@angular/common';
import { Component, signal } from '@angular/core';
import { NavigationEnd, Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { filter } from 'rxjs';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, NgClass],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  currentUrl = '/home';
  readonly theme = signal<'light' | 'dark'>(this.getStoredTheme());

  constructor(private readonly router: Router) {
    this.applyTheme(this.theme());
    this.currentUrl = this.router.url;
    this.router.events
      .pipe(filter((event): event is NavigationEnd => event instanceof NavigationEnd))
      .subscribe((event: NavigationEnd) => {
        this.currentUrl = event.urlAfterRedirects;
      });
  }

  isIngestDomain(): boolean {
    return this.currentUrl.startsWith('/ingest');
  }

  toggleTheme(): void {
    const next = this.theme() === 'dark' ? 'light' : 'dark';
    this.theme.set(next);
    this.applyTheme(next);
    localStorage.setItem('infohub.theme', next);
  }

  isDarkTheme(): boolean {
    return this.theme() === 'dark';
  }

  private applyTheme(theme: 'light' | 'dark'): void {
    document.documentElement.setAttribute('data-theme', theme);
  }

  private getStoredTheme(): 'light' | 'dark' {
    const stored = localStorage.getItem('infohub.theme');
    if (stored === 'dark' || stored === 'light') {
      return stored;
    }
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
}
