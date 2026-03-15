import { Component, inject, signal, computed, OnInit } from '@angular/core';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { WorkflowApiService } from '../../../services/workflow-api.service';
import { FALLBACK_WORKFLOWS } from '../../../fallback-workflow-data';
import { StatusBadgeComponent } from '../../../shared/components/status-badge/status-badge.component';
import { LoadingSkeletonComponent } from '../../../shared/components/loading-skeleton/loading-skeleton.component';
import { EmptyStateComponent } from '../../../shared/components/empty-state/empty-state.component';
import { RelativeTimePipe } from '../../../shared/pipes/relative-time.pipe';
import { WorkflowSummary } from '../../../models';

type SortOption = 'name-asc' | 'name-desc' | 'last-executed' | 'status';

@Component({
  selector: 'app-workflow-catalog-page',
  standalone: true,
  imports: [RouterLink, FormsModule, StatusBadgeComponent, LoadingSkeletonComponent, EmptyStateComponent, RelativeTimePipe],
  templateUrl: './workflow-catalog-page.component.html',
  styleUrl: './workflow-catalog-page.component.css',
})
export class WorkflowCatalogPageComponent implements OnInit {
  private readonly api = inject(WorkflowApiService);

  readonly loading = signal(true);
  readonly workflows = signal<WorkflowSummary[]>([]);
  readonly searchQuery = signal('');
  readonly sortBy = signal<SortOption>('name-asc');
  readonly apiConnected = signal(true);

  readonly filteredWorkflows = computed(() => {
    let items = this.workflows();
    const q = this.searchQuery().toLowerCase().trim();
    if (q) {
      items = items.filter(w =>
        w.display_name.toLowerCase().includes(q) ||
        w.short_description.toLowerCase().includes(q)
      );
    }

    const sort = this.sortBy();
    return [...items].sort((a, b) => {
      switch (sort) {
        case 'name-asc': return a.display_name.localeCompare(b.display_name);
        case 'name-desc': return b.display_name.localeCompare(a.display_name);
        case 'last-executed':
          return (b.last_execution.started_at || '').localeCompare(a.last_execution.started_at || '');
        case 'status':
          return a.last_execution.status.localeCompare(b.last_execution.status);
        default: return 0;
      }
    });
  });

  ngOnInit(): void {
    this.loadWorkflows();
  }

  reload(): void {
    this.loading.set(true);
    this.loadWorkflows();
  }

  onSearch(value: string): void {
    this.searchQuery.set(value);
  }

  onSort(value: string): void {
    this.sortBy.set(value as SortOption);
  }

  statusBarColor(status: string): string {
    const n = (status || '').toUpperCase();
    if (n.includes('COMPLETE')) return 'var(--ih-success-text)';
    if (n.includes('IN_PROGRESS')) return 'var(--ih-warn-text)';
    if (n.includes('FAILED')) return 'var(--ih-danger-text)';
    return 'var(--ih-border)';
  }

  private loadWorkflows(): void {
    this.api.getWorkflows('ingest').subscribe({
      next: items => {
        this.workflows.set(items);
        this.apiConnected.set(true);
        this.loading.set(false);
      },
      error: () => {
        this.workflows.set(FALLBACK_WORKFLOWS);
        this.apiConnected.set(false);
        this.loading.set(false);
      },
    });
  }
}
