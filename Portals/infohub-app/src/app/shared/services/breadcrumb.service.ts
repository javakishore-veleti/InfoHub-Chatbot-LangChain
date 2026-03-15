import { Injectable, signal } from '@angular/core';
import { ActivatedRouteSnapshot, NavigationEnd, Router } from '@angular/router';
import { filter } from 'rxjs';

export interface BreadcrumbSegment {
  label: string;
  path: string;
  icon?: string;
}

@Injectable({ providedIn: 'root' })
export class BreadcrumbService {
  readonly segments = signal<BreadcrumbSegment[]>([]);

  constructor(private readonly router: Router) {
    this.router.events
      .pipe(filter((e): e is NavigationEnd => e instanceof NavigationEnd))
      .subscribe(() => this.buildBreadcrumbs());
  }

  private buildBreadcrumbs(): void {
    const segments: BreadcrumbSegment[] = [];
    let route: ActivatedRouteSnapshot | null = this.router.routerState.snapshot.root;

    while (route) {
      if (route.data['breadcrumb']) {
        if (route.data['parent'] && !segments.find(s => s.label === route!.data['parent'])) {
          segments.push({ label: route.data['parent'], path: '' });
        }
        const path = '/' + route.pathFromRoot
          .filter(r => r.url.length)
          .map(r => r.url.map(s => s.path).join('/'))
          .join('/');
        segments.push({
          label: route.data['breadcrumb'],
          path,
          icon: route.data['icon'],
        });
      }
      route = route.firstChild;
    }

    this.segments.set(segments);
  }
}
