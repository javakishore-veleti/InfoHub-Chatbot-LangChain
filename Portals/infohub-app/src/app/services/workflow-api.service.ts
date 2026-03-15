import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import { ExecutionDetail, ExecutionPage, ExecutionSummary, WorkflowDetail, WorkflowSummary } from '../models';

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
}

