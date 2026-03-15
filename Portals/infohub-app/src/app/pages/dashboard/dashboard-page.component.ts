import { Component, inject, signal, OnInit } from '@angular/core';
import { RouterLink } from '@angular/router';

import { WorkflowApiService } from '../../services/workflow-api.service';
import { StatusBadgeComponent } from '../../shared/components/status-badge/status-badge.component';
import { LoadingSkeletonComponent } from '../../shared/components/loading-skeleton/loading-skeleton.component';
import { RelativeTimePipe } from '../../shared/pipes/relative-time.pipe';
import { ExecutionSummary, WorkflowSummary } from '../../models';

@Component({
  selector: 'app-dashboard-page',
  standalone: true,
  imports: [RouterLink, StatusBadgeComponent, LoadingSkeletonComponent, RelativeTimePipe],
  templateUrl: './dashboard-page.component.html',
  styleUrl: './dashboard-page.component.css',
})
export class DashboardPageComponent implements OnInit {
  private readonly api = inject(WorkflowApiService);

  readonly loading = signal(true);
  readonly recentExecutions = signal<ExecutionSummary[]>([]);
  readonly workflows = signal<WorkflowSummary[]>([]);
  readonly totalExec = signal(0);
  readonly completedCount = signal(0);
  readonly failedCount = signal(0);
  readonly inProgressCount = signal(0);

  ngOnInit(): void {
    this.api.getExecutions({ module_name: 'ingest', page: 1, page_size: 5 }).subscribe({
      next: data => {
        this.recentExecutions.set(data.items);
        this.totalExec.set(data.total_items);
        this.completedCount.set(data.items.filter(e => e.status === 'COMPLETED').length);
        this.failedCount.set(data.items.filter(e => e.status === 'FAILED').length);
        this.inProgressCount.set(data.items.filter(e => e.status === 'IN_PROGRESS').length);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });

    this.api.getWorkflows('ingest').subscribe({
      next: items => this.workflows.set(items),
      error: () => {},
    });
  }
}
