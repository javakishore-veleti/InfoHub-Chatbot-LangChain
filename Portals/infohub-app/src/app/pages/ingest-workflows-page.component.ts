import { AsyncPipe, DatePipe, NgClass } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { catchError, map, of } from 'rxjs';

import { FALLBACK_WORKFLOWS } from '../fallback-workflow-data';
import { WorkflowSummary } from '../models';
import { WorkflowApiService } from '../services/workflow-api.service';

@Component({
  selector: 'app-ingest-workflows-page',
  standalone: true,
  imports: [AsyncPipe, DatePipe, RouterLink, NgClass],
  template: `
    <section class="content-card">
      <div class="d-flex flex-wrap justify-content-between align-items-start gap-3 mb-3">
        <div>
          <h2 class="page-heading">Ingest Workflow Catalog</h2>
          <p class="page-subtitle">Select a workflow, inspect its metadata, and launch runs with confidence.</p>
        </div>
        <button class="btn btn-outline-primary" type="button" (click)="reload()">
          <i class="fa-solid fa-rotate-right me-2"></i>Refresh
        </button>
      </div>

      <div class="row g-3 mb-3">
        <div class="col-sm-6 col-xl-4">
          <div class="metric-card h-100">
            <div class="metric-label">Domain</div>
            <div class="metric-value"><i class="fa-solid fa-inbox me-2 text-primary"></i>Ingest</div>
          </div>
        </div>
        <div class="col-sm-6 col-xl-4">
          <div class="metric-card h-100">
            <div class="metric-label">Workflows</div>
            <div class="metric-value"><i class="fa-solid fa-diagram-project me-2 text-primary"></i>{{ workflowCount() }}</div>
          </div>
        </div>
        <div class="col-sm-6 col-xl-4">
          <div class="metric-card h-100">
            <div class="metric-label">Connection</div>
            <div class="metric-value">
              <i class="fa-solid" [ngClass]="apiConnected() ? 'fa-plug-circle-check text-success' : 'fa-plug-circle-xmark text-warning'"></i>
              <span class="ms-2">{{ apiConnected() ? 'Live API' : 'Fallback Mode' }}</span>
            </div>
          </div>
        </div>
      </div>

      @if (!apiConnected()) {
        <div class="alert info-alert mb-3">
          <div class="fw-semibold mb-1"><i class="fa-solid fa-triangle-exclamation me-2"></i>Backend API is unavailable.</div>
          <div class="small">Showing fallback workflow metadata so your UI remains usable during local setup.</div>
          <pre class="mb-0 mt-2"><code>npm run start:api
npm run start:api-ui</code></pre>
        </div>
      }

      @if (error()) {
        <div class="alert alert-danger py-2">{{ error() }}</div>
      }

      @if (workflows$ | async; as workflows) {
        <div class="row g-3">
          @for (workflow of workflows; track workflow.workflow_id) {
            <div class="col-lg-6 col-xxl-4">
              <article class="workflow-card card h-100">
                <div class="card-body d-flex flex-column gap-2">
                  <div class="d-flex justify-content-between align-items-start gap-2">
                    <div class="d-flex gap-2">
                      <span class="icon-pill"><i class="fa-solid fa-diagram-project"></i></span>
                      <div>
                        <h3 class="h5 card-title">{{ workflow.display_name }}</h3>
                        <p class="text-secondary mb-0 small">{{ workflow.short_description }}</p>
                      </div>
                    </div>
                    <span [ngClass]="statusClass(workflow.last_execution.status)">
                      <i class="fa-solid" [ngClass]="statusIcon(workflow.last_execution.status)"></i>
                      {{ workflow.last_execution.status }}
                    </span>
                  </div>

                  <div class="meta-line"><i class="fa-solid fa-hashtag me-2"></i>Selector: <code>{{ workflow.workflow_selector }}</code></div>
                  <div class="meta-line"><i class="fa-solid fa-fingerprint me-2"></i>Workflow ID: <code>{{ workflow.workflow_id }}</code></div>

                  @if (workflow.last_execution.started_at) {
                    <div class="meta-line">
                      <i class="fa-solid fa-calendar-check me-2"></i>Last Started: {{ workflow.last_execution.started_at | date: 'medium' }}
                    </div>
                  }

                  <div class="mt-auto pt-1">
                    <a class="btn btn-primary w-100" [routerLink]="['/ingest/run']" [queryParams]="{ workflow: workflow.workflow_selector }">
                      <i class="fa-solid fa-play me-2"></i>Run Workflow
                    </a>
                  </div>
                </div>
              </article>
            </div>
          }
        </div>
      }
    </section>
  `,
})
export class IngestWorkflowsPageComponent {
  private readonly api = inject(WorkflowApiService);

  readonly error = signal<string | null>(null);
  readonly apiConnected = signal(true);
  readonly workflowCount = signal(0);

  private readonly loadWorkflows = () =>
    this.api.getWorkflows('ingest').pipe(
      map((items: WorkflowSummary[]) => items.sort((a: WorkflowSummary, b: WorkflowSummary) => a.display_name.localeCompare(b.display_name))),
      map((items: WorkflowSummary[]) => {
        this.workflowCount.set(items.length);
        this.apiConnected.set(true);
        this.error.set(null);
        return items;
      }),
      catchError((err: unknown) => {
        const detail = typeof err === 'object' && err !== null && 'error' in err ? (err as { error?: { detail?: string } }).error?.detail : null;
        this.error.set(detail ?? 'Unable to load workflows from API.');
        this.apiConnected.set(false);
        this.workflowCount.set(FALLBACK_WORKFLOWS.length);
        return of(FALLBACK_WORKFLOWS);
      }),
    );

  workflows$ = this.loadWorkflows();

  reload(): void {
    this.workflows$ = this.loadWorkflows();
  }

  statusClass(status: string): string {
    const normalized = (status || '').toUpperCase();
    if (normalized.includes('COMPLETE')) {
      return 'status-badge status-success';
    }
    if (normalized.includes('IN_PROGRESS')) {
      return 'status-badge status-warning';
    }
    if (normalized.includes('FAILED')) {
      return 'status-badge status-danger';
    }
    return 'status-badge status-neutral';
  }

  statusIcon(status: string): string {
    const normalized = (status || '').toUpperCase();
    if (normalized.includes('COMPLETE')) {
      return 'fa-circle-check';
    }
    if (normalized.includes('IN_PROGRESS')) {
      return 'fa-hourglass-half';
    }
    if (normalized.includes('FAILED')) {
      return 'fa-triangle-exclamation';
    }
    return 'fa-circle-minus';
  }
}

