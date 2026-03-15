import { Component, inject, signal, OnInit } from '@angular/core';
import { RouterLink } from '@angular/router';
import { DatePipe, SlicePipe } from '@angular/common';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { WorkflowApiService } from '../../../services/workflow-api.service';
import { StatusBadgeComponent } from '../../../shared/components/status-badge/status-badge.component';
import { LoadingSkeletonComponent } from '../../../shared/components/loading-skeleton/loading-skeleton.component';
import { EmptyStateComponent } from '../../../shared/components/empty-state/empty-state.component';
import { RelativeTimePipe } from '../../../shared/pipes/relative-time.pipe';
import { ExecutionPage } from '../../../models';

@Component({
  selector: 'app-execution-history-page',
  standalone: true,
  imports: [RouterLink, DatePipe, SlicePipe, ReactiveFormsModule, StatusBadgeComponent, LoadingSkeletonComponent, EmptyStateComponent, RelativeTimePipe],
  templateUrl: './execution-history-page.component.html',
  styleUrl: './execution-history-page.component.css',
})
export class ExecutionHistoryPageComponent implements OnInit {
  private readonly api = inject(WorkflowApiService);
  private readonly fb = inject(FormBuilder);

  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly pageData = signal<ExecutionPage>({ items: [], page: 1, page_size: 15, total_items: 0, total_pages: 1 });
  readonly workflowOptions = signal<Array<{ workflow_id: string; display_name: string }>>([]);

  readonly filtersForm = this.fb.group({
    workflow_id: [''],
    status: [''],
    started_from: [''],
    started_to: [''],
  });

  ngOnInit(): void {
    this.api.getWorkflows('ingest').subscribe({
      next: wfs => this.workflowOptions.set(wfs.map(w => ({ workflow_id: w.workflow_id, display_name: w.display_name }))),
      error: () => {},
    });
    this.fetchPage(1);
  }

  refresh(page: number): void {
    this.fetchPage(page);
  }

  applyFilters(): void {
    this.fetchPage(1);
  }

  clearFilters(): void {
    this.filtersForm.reset({ workflow_id: '', status: '', started_from: '', started_to: '' });
    this.fetchPage(1);
  }

  pageNumbers(): (number | '...')[] {
    const data = this.pageData();
    const total = data.total_pages || 1;
    const current = data.page;
    const pages: (number | '...')[] = [];

    if (total <= 7) {
      for (let i = 1; i <= total; i++) pages.push(i);
      return pages;
    }

    pages.push(1);
    if (current > 3) pages.push('...');
    for (let i = Math.max(2, current - 1); i <= Math.min(total - 1, current + 1); i++) {
      pages.push(i);
    }
    if (current < total - 2) pages.push('...');
    pages.push(total);

    return pages;
  }

  private fetchPage(page: number): void {
    this.loading.set(true);
    const v = this.filtersForm.value;
    this.api.getExecutions({
      module_name: 'ingest',
      workflow_id: v.workflow_id || undefined,
      status: v.status || undefined,
      started_from: v.started_from || undefined,
      started_to: v.started_to || undefined,
      page,
      page_size: 15,
    }).subscribe({
      next: data => {
        this.pageData.set(data);
        this.error.set(null);
        this.loading.set(false);
      },
      error: err => {
        this.error.set(err?.error?.detail ?? 'Unable to load executions.');
        this.pageData.set({ items: [], page, page_size: 15, total_items: 0, total_pages: 1 });
        this.loading.set(false);
      },
    });
  }
}
