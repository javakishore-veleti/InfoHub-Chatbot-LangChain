import { Routes } from '@angular/router';

export const routes: Routes = [
  {
	path: '',
	pathMatch: 'full',
	redirectTo: 'home',
  },
  {
	path: 'home',
	loadComponent: () => import('./pages/home-page.component').then((m) => m.HomePageComponent),
  },
  {
	path: 'ingest/workflows',
	loadComponent: () => import('./pages/ingest-workflows-page.component').then((m) => m.IngestWorkflowsPageComponent),
  },
  {
	path: 'ingest/run',
	loadComponent: () => import('./pages/ingest-run-page.component').then((m) => m.IngestRunPageComponent),
  },
  {
	path: 'ingest/executions',
	loadComponent: () => import('./pages/ingest-executions-page.component').then((m) => m.IngestExecutionsPageComponent),
  },
  {
	path: 'model-build',
	loadComponent: () => import('./pages/model-build-page.component').then((m) => m.ModelBuildPageComponent),
  },
  {
	path: 'administration',
	loadComponent: () => import('./pages/administration-page.component').then((m) => m.AdministrationPageComponent),
  },
  {
	path: '**',
	redirectTo: 'home',
  },
];
