import { Component, inject, signal, OnInit } from '@angular/core';
import { RouterLink } from '@angular/router';
import { DatePipe, DecimalPipe } from '@angular/common';
import { WorkflowApiService } from '../../../services/workflow-api.service';
import { StatusBadgeComponent } from '../../../shared/components/status-badge/status-badge.component';
import { LoadingSkeletonComponent } from '../../../shared/components/loading-skeleton/loading-skeleton.component';
import { EmptyStateComponent } from '../../../shared/components/empty-state/empty-state.component';
import { RelativeTimePipe } from '../../../shared/pipes/relative-time.pipe';
import { DatasetOverviewPage } from '../../../models';

@Component({
  selector: 'app-crawled-datasets-page',
  standalone: true,
  imports: [RouterLink, DatePipe, DecimalPipe, StatusBadgeComponent, LoadingSkeletonComponent, EmptyStateComponent, RelativeTimePipe],
  templateUrl: './crawled-datasets-page.component.html',
  styleUrl: './crawled-datasets-page.component.css',
})
export class CrawledDatasetsPageComponent implements OnInit {
  private readonly api = inject(WorkflowApiService);

  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly pageData = signal<DatasetOverviewPage>({ items: [], page: 1, page_size: 20, total_items: 0, total_pages: 1 });

  ngOnInit(): void {
    this.fetchPage(1);
  }

  refresh(page: number): void {
    this.fetchPage(page);
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
    this.api.getDatasets(page, 20).subscribe({
      next: data => {
        this.pageData.set(data);
        this.error.set(null);
        this.loading.set(false);
      },
      error: err => {
        this.error.set(err?.error?.detail ?? 'Unable to load datasets.');
        this.pageData.set({ items: [], page, page_size: 20, total_items: 0, total_pages: 1 });
        this.loading.set(false);
      },
    });
  }
}
