import { Component, inject, signal, OnInit } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { WorkflowApiService } from '../../../services/workflow-api.service';
import { LoadingSkeletonComponent } from '../../../shared/components/loading-skeleton/loading-skeleton.component';
import { DatasetFileDetail } from '../../../models';

@Component({
  selector: 'app-file-detail-page',
  standalone: true,
  imports: [RouterLink, LoadingSkeletonComponent],
  templateUrl: './file-detail-page.component.html',
  styleUrl: './file-detail-page.component.css',
})
export class FileDetailPageComponent implements OnInit {
  private readonly api = inject(WorkflowApiService);
  private readonly route = inject(ActivatedRoute);

  readonly workflowId = signal('');
  readonly fileId = signal('');
  readonly folderType = signal('crawled_pages');
  readonly runFolder = signal<string | null>(null);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly fileDetail = signal<DatasetFileDetail | null>(null);

  ngOnInit(): void {
    const params = this.route.snapshot.paramMap;
    const query = this.route.snapshot.queryParamMap;

    this.workflowId.set(params.get('workflowId') || '');
    this.fileId.set(params.get('fileId') || '');
    this.folderType.set(query.get('folder_type') || 'crawled_pages');
    this.runFolder.set(query.get('run_folder'));

    this.api.getDatasetFileDetail(
      this.workflowId(),
      this.fileId(),
      this.folderType(),
      this.runFolder() || undefined,
    ).subscribe({
      next: detail => {
        this.fileDetail.set(detail);
        this.loading.set(false);
      },
      error: err => {
        this.error.set(err?.error?.detail ?? 'Unable to load file content.');
        this.loading.set(false);
      },
    });
  }

  formatSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1048576).toFixed(1)} MB`;
  }

  formatJson(content: Record<string, unknown>): string {
    return JSON.stringify(content, null, 2);
  }

  folderTypeLabel(): string {
    return this.folderType().replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  }
}
