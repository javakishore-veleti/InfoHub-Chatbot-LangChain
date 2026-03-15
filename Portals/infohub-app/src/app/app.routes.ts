import { Routes } from '@angular/router';
import { ShellComponent } from './layout/shell/shell.component';

export const routes: Routes = [
  {
    path: '',
    component: ShellComponent,
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'dashboard' },
      {
        path: 'dashboard',
        loadComponent: () =>
          import('./pages/dashboard/dashboard-page.component').then(m => m.DashboardPageComponent),
        data: { breadcrumb: 'Dashboard', icon: 'fa-gauge-high' },
      },
      {
        path: 'ingest/workflows',
        loadComponent: () =>
          import('./pages/ingest/workflow-catalog/workflow-catalog-page.component').then(m => m.WorkflowCatalogPageComponent),
        data: { breadcrumb: 'Workflow Catalog', parent: 'Ingest', icon: 'fa-diagram-project' },
      },
      {
        path: 'ingest/run',
        loadComponent: () =>
          import('./pages/ingest/workflow-run/workflow-run-page.component').then(m => m.WorkflowRunPageComponent),
        data: { breadcrumb: 'Run Workflow', parent: 'Ingest', icon: 'fa-play' },
      },
      {
        path: 'ingest/executions',
        loadComponent: () =>
          import('./pages/ingest/execution-history/execution-history-page.component').then(m => m.ExecutionHistoryPageComponent),
        data: { breadcrumb: 'Execution History', parent: 'Ingest', icon: 'fa-clock-rotate-left' },
      },
      {
        path: 'ingest/executions/:executionId',
        loadComponent: () =>
          import('./pages/ingest/execution-detail/execution-detail-page.component').then(m => m.ExecutionDetailPageComponent),
        data: { breadcrumb: 'Execution Detail', parent: 'Ingest', icon: 'fa-magnifying-glass' },
      },
      { path: '**', redirectTo: 'dashboard' },
    ],
  },
];
