import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import {
  DatasetFileDetail,
  DatasetFilePage,
  DatasetOverviewPage,
  ExecutionDetail,
  ExecutionPage,
  ExecutionSummary,
  FolderTypeInfo,
  RunFolderInfo,
  WorkflowDetail,
  WorkflowSummary,
} from '../models';

const API_BASE = 'http://localhost:8000/api/v1';

@Injectable({ providedIn: 'root' })
export class WorkflowApiService {
  constructor(private readonly http: HttpClient) {}

  checkApiHealth(): Observable<{ status: string }> {
    return this.http.get<{ status: string }>(`${API_BASE}/health`);
  }

  getWorkflows(domain?: string): Observable<WorkflowSummary[]> {
    let params = new HttpParams();
    if (domain) {
      params = params.set('domain', domain);
    }
    return this.http.get<WorkflowSummary[]>(`${API_BASE}/workflows`, { params });
  }

  getWorkflowDetail(selector: string): Observable<WorkflowDetail> {
    const encoded = selector
      .split('/')
      .map((part) => encodeURIComponent(part))
      .join('/');
    return this.http.get<WorkflowDetail>(`${API_BASE}/workflows/${encoded}`);
  }

  runIngestWorkflow(selector: string, inputs: Record<string, unknown>): Observable<ExecutionSummary> {
    const encoded = selector
      .split('/')
      .map((part) => encodeURIComponent(part))
      .join('/');
    return this.http.post<ExecutionSummary>(`${API_BASE}/ingest/runs/${encoded}`, { inputs });
  }

  getExecutions(filters: {
    module_name?: string;
    workflow_id?: string;
    status?: string;
    started_from?: string;
    started_to?: string;
    page?: number;
    page_size?: number;
  }): Observable<ExecutionPage> {
    let params = new HttpParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && `${value}`.length > 0) {
        params = params.set(key, `${value}`);
      }
    });
    return this.http.get<ExecutionPage>(`${API_BASE}/executions`, { params });
  }

  getExecution(executionId: string): Observable<ExecutionDetail> {
    return this.http.get<ExecutionDetail>(`${API_BASE}/executions/${encodeURIComponent(executionId)}`);
  }

  /* ── Datalake ────────────────────────────────── */

  getDatasets(page = 1, pageSize = 20): Observable<DatasetOverviewPage> {
    const params = new HttpParams().set('page', `${page}`).set('page_size', `${pageSize}`);
    return this.http.get<DatasetOverviewPage>(`${API_BASE}/datalake/datasets`, { params });
  }

  getDatasetRuns(workflowId: string): Observable<RunFolderInfo[]> {
    return this.http.get<RunFolderInfo[]>(`${API_BASE}/datalake/datasets/${encodeURIComponent(workflowId)}/runs`);
  }

  getDatasetFolderTypes(workflowId: string, runFolder?: string): Observable<FolderTypeInfo[]> {
    let params = new HttpParams();
    if (runFolder) params = params.set('run_folder', runFolder);
    return this.http.get<FolderTypeInfo[]>(
      `${API_BASE}/datalake/datasets/${encodeURIComponent(workflowId)}/folder-types`,
      { params },
    );
  }

  getDatasetFiles(
    workflowId: string,
    options: { page?: number; page_size?: number; folder_type?: string; run_folder?: string },
  ): Observable<DatasetFilePage> {
    let params = new HttpParams();
    if (options.page) params = params.set('page', `${options.page}`);
    if (options.page_size) params = params.set('page_size', `${options.page_size}`);
    if (options.folder_type) params = params.set('folder_type', options.folder_type);
    if (options.run_folder) params = params.set('run_folder', options.run_folder);
    return this.http.get<DatasetFilePage>(
      `${API_BASE}/datalake/datasets/${encodeURIComponent(workflowId)}/files`,
      { params },
    );
  }

  getDatasetFileDetail(
    workflowId: string,
    fileId: string,
    folderType: string,
    runFolder?: string,
  ): Observable<DatasetFileDetail> {
    let params = new HttpParams().set('folder_type', folderType);
    if (runFolder) params = params.set('run_folder', runFolder);
    return this.http.get<DatasetFileDetail>(
      `${API_BASE}/datalake/datasets/${encodeURIComponent(workflowId)}/files/${encodeURIComponent(fileId)}`,
      { params },
    );
  }
}

