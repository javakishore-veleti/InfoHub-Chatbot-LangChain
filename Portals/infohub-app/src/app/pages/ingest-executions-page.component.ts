import { AsyncPipe, DatePipe, NgClass } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { Observable, catchError, map, of, switchMap, tap } from 'rxjs';

import { ExecutionPage } from '../models';

import { WorkflowApiService } from '../services/workflow-api.service';

@Component({
  selector: 'app-ingest-executions-page',
  standalone: true,
  imports: [ReactiveFormsModule, AsyncPipe, DatePipe, NgClass],
  template: `
    <section class="content-card">
      <div class="d-flex flex-wrap justify-content-between align-items-start gap-3 mb-3">
        <div>
          <h2 class="page-heading">Ingest Executions</h2>
          <p class="page-subtitle">Track run history, filter by workflow and status, and review recent operational activity.</p>
        </div>
        <div class="btn-group" role="group" aria-label="Table density">
          <button
            type="button"
            class="btn"
            [ngClass]="density() === 'comfortable' ? 'btn-primary' : 'btn-outline-primary'"
            (click)="setDensity('comfortable')"
          >
            <i class="fa-solid fa-table-cells-large me-1"></i>Comfortable
          </button>
          <button
            type="button"
            class="btn"
            [ngClass]="density() === 'compact' ? 'btn-primary' : 'btn-outline-primary'"
            (click)="setDensity('compact')"
          >
            <i class="fa-solid fa-table-cells me-1"></i>Compact
          </button>
        </div>
      </div>

      <form [formGroup]="filtersForm" (ngSubmit)="refresh(1)" class="sticky-toolbar p-3 mb-3">
        <div class="row g-3 align-items-end">
          <div class="col-md-6 col-xl-3">
            <label class="form-label fw-semibold">Workflow</label>
            <select class="form-select" formControlName="workflow_id">
              <option value="">All</option>
              @for (item of workflowOptions(); track item.workflow_id) {
                <option [value]="item.workflow_id">{{ item.display_name }} ({{ item.workflow_id }})</option>
              }
            </select>
          </div>
          <div class="col-md-6 col-xl-2">
            <label class="form-label fw-semibold">Status</label>
            <select class="form-select" formControlName="status">
              <option value="">All</option>
              <option>IN_PROGRESS</option>
              <option>COMPLETED</option>
              <option>FAILED</option>
              <option>SKIPPED</option>
              <option>Never Executed</option>
            </select>
          </div>
          <div class="col-md-6 col-xl-3">
            <label class="form-label fw-semibold">Started From</label>
            <input class="form-control" type="datetime-local" formControlName="started_from" />
          </div>
          <div class="col-md-6 col-xl-3">
            <label class="form-label fw-semibold">Started To</label>
            <input class="form-control" type="datetime-local" formControlName="started_to" />
          </div>
          <div class="col-xl-1 d-grid gap-2">
            <button class="btn btn-primary" type="submit"><i class="fa-solid fa-filter me-1"></i>Apply</button>
            <button class="btn btn-outline-secondary" type="button" (click)="clear()">Clear</button>
          </div>
        </div>
      </form>

      @if (error()) {
        <div class="alert alert-danger py-2">{{ error() }}</div>
      }

      @if (pageData$ | async; as pageData) {
        <p class="table-note mb-2">
          Showing page {{ pageData.page }} of {{ pageData.total_pages || 1 }} ({{ pageData.total_items }} total executions)
        </p>
        <div class="execution-table-wrap">
          <table class="table table-hover execution-table" [ngClass]="density() === 'compact' ? 'compact-density' : 'comfortable-density'">
            <thead>
              <tr>
                <th>Execution ID</th>
                <th>Workflow</th>
                <th>Status</th>
                <th>Started</th>
                <th>Completed</th>
                <th>Run Folder</th>
              </tr>
            </thead>
            <tbody>
              @for (row of pageData.items; track row.execution_id) {
                <tr>
                  <td><code>{{ row.execution_id }}</code></td>
                  <td>
                    <div class="fw-semibold">{{ row.display_name }}</div>
                    <small class="text-secondary">{{ row.workflow_id }}</small>
                  </td>
                  <td>
                    <span [ngClass]="statusClass(row.status)">
                      <i class="fa-solid" [ngClass]="statusIcon(row.status)"></i>
                      {{ row.status }}
                    </span>
                  </td>
                  <td>{{ row.started_at | date: 'medium' }}</td>
                  <td>{{ row.completed_at ? (row.completed_at | date: 'medium') : '-' }}</td>
                  <td>{{ row.active_run_folder || '-' }}</td>
                </tr>
              }
              @if (!pageData.items.length) {
                <tr>
                  <td colspan="6" class="text-center py-4">
                    <div class="empty-state p-3">
                      <i class="fa-regular fa-folder-open me-2"></i>No executions found for this filter set.
                    </div>
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>

        <div class="d-flex flex-wrap justify-content-between align-items-center gap-2 mt-3">
          <button class="btn btn-outline-secondary" type="button" [disabled]="pageData.page <= 1" (click)="refresh(pageData.page - 1)">
            <i class="fa-solid fa-arrow-left me-1"></i>Previous
          </button>
          <span class="small text-secondary">Page {{ pageData.page }} / {{ pageData.total_pages || 1 }}</span>
          <button class="btn btn-outline-secondary" type="button" [disabled]="pageData.page >= pageData.total_pages" (click)="refresh(pageData.page + 1)">
            Next<i class="fa-solid fa-arrow-right ms-1"></i>
          </button>
        </div>
      }
    </section>
  `,
})
export class IngestExecutionsPageComponent {
  private readonly api = inject(WorkflowApiService);
  private readonly fb = inject(FormBuilder);

  readonly error = signal<string | null>(null);
  readonly workflowOptions = signal<Array<{ workflow_id: string; display_name: string }>>([]);
  readonly page = signal(1);
  readonly density = signal<'compact' | 'comfortable'>(this.readDensity());

  readonly filtersForm = this.fb.group({
    workflow_id: [''],
    status: [''],
    started_from: [''],
    started_to: [''],
  });

  pageData$: Observable<ExecutionPage> = this.api.getWorkflows('ingest').pipe(
    tap((workflows) => {
      this.workflowOptions.set(workflows.map((workflow) => ({ workflow_id: workflow.workflow_id, display_name: workflow.display_name })));
    }),
    switchMap(() => this.fetchPage(this.page())),
    catchError((err) => {
      this.error.set(err?.error?.detail ?? 'Unable to load executions.');
      return of({ items: [], page: 1, page_size: 15, total_items: 0, total_pages: 1 });
    }),
  );

  refresh(page: number): void {
    this.page.set(page);
    this.pageData$ = this.fetchPage(page);
  }

  clear(): void {
    this.filtersForm.reset({ workflow_id: '', status: '', started_from: '', started_to: '' });
    this.refresh(1);
  }

  setDensity(value: 'compact' | 'comfortable'): void {
    this.density.set(value);
    localStorage.setItem('infohub.executions.density', value);
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

  private readDensity(): 'compact' | 'comfortable' {
    const stored = localStorage.getItem('infohub.executions.density');
    return stored === 'compact' ? 'compact' : 'comfortable';
  }

  private fetchPage(page: number) {
    const values = this.filtersForm.value;
    return this.api
      .getExecutions({
        module_name: 'ingest',
        workflow_id: values.workflow_id || undefined,
        status: values.status || undefined,
        started_from: values.started_from || undefined,
        started_to: values.started_to || undefined,
        page,
        page_size: 15,
      })
      .pipe(
        map((data) => {
          this.error.set(null);
          return data;
        }),
        catchError((err) => {
          this.error.set(err?.error?.detail ?? 'Unable to load executions.');
          return of({ items: [], page, page_size: 15, total_items: 0, total_pages: 1 });
        }),
      );
  }
}





