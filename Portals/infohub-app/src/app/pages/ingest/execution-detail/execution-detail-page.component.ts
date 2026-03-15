import { Component, inject, signal, OnInit } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { DatePipe, JsonPipe } from '@angular/common';
import { WorkflowApiService } from '../../../services/workflow-api.service';
import { StatusBadgeComponent } from '../../../shared/components/status-badge/status-badge.component';
import { LoadingSkeletonComponent } from '../../../shared/components/loading-skeleton/loading-skeleton.component';
import { RelativeTimePipe } from '../../../shared/pipes/relative-time.pipe';
import { ExecutionDetail } from '../../../models';

@Component({
  selector: 'app-execution-detail-page',
  standalone: true,
  imports: [RouterLink, DatePipe, JsonPipe, StatusBadgeComponent, LoadingSkeletonComponent, RelativeTimePipe],
  templateUrl: './execution-detail-page.component.html',
  styleUrl: './execution-detail-page.component.css',
})
export class ExecutionDetailPageComponent implements OnInit {
  private readonly api = inject(WorkflowApiService);
  private readonly route = inject(ActivatedRoute);

  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly execution = signal<ExecutionDetail | null>(null);
  readonly activeTab = signal<'overview' | 'request' | 'response'>('overview');

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('executionId');
    if (!id) {
      this.error.set('No execution ID provided.');
      this.loading.set(false);
      return;
    }

    this.api.getExecution(id).subscribe({
      next: exec => {
        this.execution.set(exec);
        this.loading.set(false);
      },
      error: err => {
        this.error.set(err?.error?.detail ?? 'Unable to load execution details.');
        this.loading.set(false);
      },
    });
  }

  computeDuration(): string {
    const exec = this.execution();
    if (!exec?.started_at || !exec?.completed_at) return '-';
    const start = new Date(exec.started_at).getTime();
    const end = new Date(exec.completed_at).getTime();
    const seconds = Math.floor((end - start) / 1000);
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remaining = seconds % 60;
    return `${minutes}m ${remaining}s`;
  }
}
