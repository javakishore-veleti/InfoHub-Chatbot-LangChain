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
      {
        path: 'datalake/datasets',
        loadComponent: () =>
          import('./pages/datalake/crawled-datasets/crawled-datasets-page.component').then(m => m.CrawledDatasetsPageComponent),
        data: { breadcrumb: 'Crawled Datasets', parent: 'Datalake', icon: 'fa-database' },
      },
      {
        path: 'datalake/datasets/:workflowId/files',
        loadComponent: () =>
          import('./pages/datalake/dataset-files/dataset-files-page.component').then(m => m.DatasetFilesPageComponent),
        data: { breadcrumb: 'Dataset Files', parent: 'Datalake', icon: 'fa-folder-open' },
      },
      {
        path: 'datalake/datasets/:workflowId/files/:fileId',
        loadComponent: () =>
          import('./pages/datalake/file-detail/file-detail-page.component').then(m => m.FileDetailPageComponent),
        data: { breadcrumb: 'File Detail', parent: 'Datalake', icon: 'fa-file-code' },
      },
      { path: '**', redirectTo: 'dashboard' },
    ],
  },
];
