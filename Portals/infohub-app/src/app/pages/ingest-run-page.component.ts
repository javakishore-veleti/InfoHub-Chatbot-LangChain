import { AsyncPipe, JsonPipe } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { catchError, of, switchMap, tap } from 'rxjs';

import { FALLBACK_WORKFLOW_DETAILS } from '../fallback-workflow-data';
import { WorkflowDetail, WorkflowFieldOption, WorkflowFieldSchema } from '../models';
import { WorkflowApiService } from '../services/workflow-api.service';

@Component({
  selector: 'app-ingest-run-page',
  standalone: true,
  imports: [AsyncPipe, ReactiveFormsModule, JsonPipe],
  template: `
    <section class="content-card">
      <div class="d-flex flex-wrap justify-content-between align-items-start gap-3 mb-3">
        <div>
          <h2 class="page-heading">Run Ingest Workflow</h2>
          <p class="page-subtitle">Dynamic input form generated directly from workflow metadata and validation rules.</p>
        </div>
      </div>

      @if (!apiConnected()) {
        <div class="alert info-alert mb-3">
          <div class="fw-semibold mb-1"><i class="fa-solid fa-triangle-exclamation me-2"></i>API unavailable.</div>
          <div>Form metadata is loaded from local fallback data.</div>
          <div class="small mt-1">Start backend to run live executions:</div>
          <pre class="mb-0 mt-2"><code>npm run start:api
npm run start:api-ui</code></pre>
        </div>
      }

      @if (error()) {
        <div class="alert alert-danger py-2">{{ error() }}</div>
      }

      @if (workflow$ | async; as workflow) {
        @if (workflow) {
          <div class="card border-0 bg-light-subtle mb-3">
            <div class="card-body">
              <div class="d-flex flex-wrap justify-content-between align-items-start gap-2">
                <div>
                  <h3 class="h4 mb-1"><i class="fa-solid fa-diagram-project me-2 text-primary"></i>{{ workflow.title }}</h3>
                  <p class="text-secondary mb-2">{{ workflow.description }}</p>
                </div>
              </div>
              <div class="small text-secondary">
                Selector: <code>{{ workflow.workflow_selector }}</code>
                <span class="mx-2">|</span>
                Workflow ID: <code>{{ workflow.workflow_id }}</code>
              </div>
            </div>
          </div>

          @if (form()) {
            <form [formGroup]="form()!" (ngSubmit)="submit(workflow)">
              <div class="row g-3 mb-3">
                @for (field of workflow.fields; track field.key) {
                  <div class="col-md-6 col-xl-4">
                    <div class="h-100 p-3 border rounded-3 bg-white">
                      <label class="form-label fw-semibold" [for]="field.key">{{ field.label }}</label>
                    @switch (field.type) {
                      @case ('textarea-list') {
                        <textarea
                          class="form-control"
                          [id]="field.key"
                          [formControlName]="field.key"
                          rows="4"
                          [placeholder]="field.description || 'One value per line'"
                        ></textarea>
                      }
                      @case ('multiselect') {
                        <select class="form-select" [id]="field.key" [formControlName]="field.key" multiple>
                          @for (option of optionsFor(field); track option.value) {
                            <option [value]="option.value">{{ option.label }}</option>
                          }
                        </select>
                      }
                      @case ('checkbox') {
                        <div class="form-check mt-1">
                          <input class="form-check-input" [id]="field.key" type="checkbox" [formControlName]="field.key" />
                        </div>
                      }
                      @default {
                        <input
                          class="form-control"
                          [id]="field.key"
                          [type]="inputType(field)"
                          [formControlName]="field.key"
                          [placeholder]="field.placeholder || ''"
                        />
                      }
                    }
                    @if (field.description) {
                      <small class="text-secondary d-block mt-2">{{ field.description }}</small>
                    }
                    </div>
                  </div>
                }
              </div>
              <div class="d-flex justify-content-end">
                <button class="btn btn-primary px-4" type="submit" [disabled]="isSubmitting() || !apiConnected()">
                  <i class="fa-solid" [class.fa-spinner]="isSubmitting()" [class.fa-spin]="isSubmitting()" [class.fa-play]="!isSubmitting()"></i>
                  <span class="ms-2">{{ isSubmitting() ? 'Running...' : 'Run Workflow' }}</span>
                </button>
              </div>
            </form>
          }
        }
      }

      @if (runResponse()) {
        <section class="mt-4">
          <h3 class="h5 mb-2"><i class="fa-solid fa-circle-check text-success me-2"></i>Execution Submitted</h3>
          <pre class="border rounded-3 bg-light p-3 mb-0">{{ runResponse() | json }}</pre>
        </section>
      }
    </section>
  `,
})
export class IngestRunPageComponent {
  private readonly api = inject(WorkflowApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly fb = inject(FormBuilder);

  readonly error = signal<string | null>(null);
  readonly apiConnected = signal(true);
  readonly form = signal<FormGroup | null>(null);
  readonly isSubmitting = signal(false);
  readonly runResponse = signal<Record<string, unknown> | null>(null);

  readonly workflow$ = this.route.queryParamMap.pipe(
    switchMap((params: import('@angular/router').ParamMap) => {
      const selector = params.get('workflow') || 'ingest/AWSBedrock';
      return this.api.getWorkflowDetail(selector).pipe(
        tap((workflow: WorkflowDetail) => {
          this.apiConnected.set(true);
          this.error.set(null);
          this.form.set(this.buildForm(workflow.fields));
        }),
      );
    }),
    catchError((err: unknown) => {
      const detail = typeof err === 'object' && err !== null && 'error' in err ? (err as { error?: { detail?: string } }).error?.detail : null;
      const fallback = FALLBACK_WORKFLOW_DETAILS['ingest/AWSBedrock'];
      this.apiConnected.set(false);
      this.error.set(detail ?? 'Unable to load workflow details from API.');
      this.form.set(this.buildForm(fallback.fields));
      return of(fallback);
    }),
  );

  optionsFor(field: WorkflowFieldSchema): WorkflowFieldOption[] {
    return field.options ?? [];
  }

  inputType(field: WorkflowFieldSchema): string {
    if (field.type === 'number') {
      return 'number';
    }
    if (field.type === 'url') {
      return 'url';
    }
    return 'text';
  }

  private buildForm(fields: WorkflowFieldSchema[]): FormGroup {
    const controls: Record<string, FormControl> = {};
    fields.forEach((field) => {
      const validators = [];
      if (field.required) {
        validators.push(Validators.required);
      }
      if (field.type === 'number') {
        if (field.min !== undefined) {
          validators.push(Validators.min(field.min));
        }
        if (field.max !== undefined) {
          validators.push(Validators.max(field.max));
        }
      }
      let defaultValue: unknown = field.default;
      if (field.type === 'textarea-list' && Array.isArray(defaultValue)) {
        defaultValue = defaultValue.join('\n');
      }
      controls[field.key] = this.fb.control(defaultValue ?? '', validators);
    });
    return this.fb.group(controls);
  }

  submit(workflow: WorkflowDetail): void {
    if (!this.apiConnected()) {
      this.error.set('API is unavailable. Start backend before submitting a workflow run.');
      return;
    }

    const form = this.form();
    if (!form || form.invalid) {
      form?.markAllAsTouched();
      return;
    }

    const inputPayload: Record<string, unknown> = {};
    for (const field of workflow.fields) {
      const value = form.get(field.key)?.value;
      if (field.type === 'textarea-list') {
        inputPayload[field.key] = String(value || '')
          .split('\n')
          .map((item) => item.trim())
          .filter((item) => item.length > 0);
      } else if (field.type === 'multiselect') {
        inputPayload[field.key] = Array.isArray(value) ? value : [];
      } else {
        inputPayload[field.key] = value;
      }
    }

    this.isSubmitting.set(true);
    this.error.set(null);
    this.runResponse.set(null);
    this.api.runIngestWorkflow(workflow.workflow_selector, inputPayload).subscribe({
      next: (response: unknown) => {
        this.runResponse.set(response as unknown as Record<string, unknown>);
        this.isSubmitting.set(false);
      },
      error: (err: unknown) => {
        const detail = typeof err === 'object' && err !== null && 'error' in err ? (err as { error?: { detail?: string } }).error?.detail : null;
        this.error.set(detail ?? 'Failed to submit workflow run.');
        this.isSubmitting.set(false);
      },
    });
  }
}

