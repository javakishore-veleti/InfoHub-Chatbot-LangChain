import { Component, inject, signal, OnInit } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { DatePipe, DecimalPipe } from '@angular/common';
import { WorkflowApiService } from '../../../services/workflow-api.service';
import { LoadingSkeletonComponent } from '../../../shared/components/loading-skeleton/loading-skeleton.component';
import { EmptyStateComponent } from '../../../shared/components/empty-state/empty-state.component';
import { DatasetFilePage, FolderTypeInfo, RunFolderInfo } from '../../../models';

@Component({
  selector: 'app-dataset-files-page',
  standalone: true,
  imports: [RouterLink, DatePipe, DecimalPipe, LoadingSkeletonComponent, EmptyStateComponent],
  templateUrl: './dataset-files-page.component.html',
  styleUrl: './dataset-files-page.component.css',
})
export class DatasetFilesPageComponent implements OnInit {
  private readonly api = inject(WorkflowApiService);
  private readonly route = inject(ActivatedRoute);

  readonly workflowId = signal('');
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly pageData = signal<DatasetFilePage>({
    items: [], page: 1, page_size: 50, total_items: 0, total_pages: 0, workflow_id: '', run_folder: null,
  });
  readonly runFolders = signal<RunFolderInfo[]>([]);
  readonly folderTypes = signal<FolderTypeInfo[]>([]);
  readonly selectedRunFolder = signal<string | null>(null);
  readonly selectedFolderType = signal('crawled_pages');

  ngOnInit(): void {
    const wfId = this.route.snapshot.paramMap.get('workflowId') || '';
    this.workflowId.set(wfId);

    // Load run folders
    this.api.getDatasetRuns(wfId).subscribe({
      next: runs => {
        this.runFolders.set(runs);
        const latest = runs.find(r => r.is_latest);
        if (latest) {
          this.selectedRunFolder.set(latest.folder_name);
        } else if (runs.length > 0) {
          this.selectedRunFolder.set(runs[0].folder_name);
        }
        this.loadFolderTypes();
      },
      error: () => this.loading.set(false),
    });
  }

  onRunFolderChange(event: Event): void {
    const value = (event.target as HTMLSelectElement).value;
    this.selectedRunFolder.set(value);
    this.loadFolderTypes();
  }

  onFolderTypeChange(folderType: string): void {
    this.selectedFolderType.set(folderType);
    this.fetchPage(1);
  }

  refresh(page: number): void {
    this.fetchPage(page);
  }

  formatSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1048576).toFixed(1)} MB`;
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

  private loadFolderTypes(): void {
    const rf = this.selectedRunFolder();
    if (!rf) {
      this.loading.set(false);
      return;
    }
    this.api.getDatasetFolderTypes(this.workflowId(), rf).subscribe({
      next: types => {
        this.folderTypes.set(types);
        if (types.length > 0 && !types.find(t => t.folder_type === this.selectedFolderType())) {
          this.selectedFolderType.set(types[0].folder_type);
        }
        this.fetchPage(1);
      },
      error: () => this.loading.set(false),
    });
  }

  private fetchPage(page: number): void {
    this.loading.set(true);
    this.api.getDatasetFiles(this.workflowId(), {
      page,
      page_size: 50,
      folder_type: this.selectedFolderType(),
      run_folder: this.selectedRunFolder() || undefined,
    }).subscribe({
      next: data => {
        this.pageData.set(data);
        this.error.set(null);
        this.loading.set(false);
      },
      error: err => {
        this.error.set(err?.error?.detail ?? 'Unable to load files.');
        this.pageData.set({
          items: [], page, page_size: 50, total_items: 0, total_pages: 0,
          workflow_id: this.workflowId(), run_folder: null,
        });
        this.loading.set(false);
      },
    });
  }
}
