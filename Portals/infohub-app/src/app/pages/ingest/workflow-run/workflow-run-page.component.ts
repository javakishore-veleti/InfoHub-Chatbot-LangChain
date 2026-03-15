import { Component, inject, signal, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { FormBuilder, FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { switchMap, catchError, tap, of } from 'rxjs';
import { WorkflowApiService } from '../../../services/workflow-api.service';
import { FALLBACK_WORKFLOW_DETAILS } from '../../../fallback-workflow-data';
import { ToastService } from '../../../shared/services/toast.service';
import { ConfirmService } from '../../../shared/services/confirm.service';
import { LoadingSkeletonComponent } from '../../../shared/components/loading-skeleton/loading-skeleton.component';
import { WorkflowDetail, WorkflowFieldOption, WorkflowFieldSchema } from '../../../models';

interface FieldSection {
  title: string;
  icon: string;
  keys: string[];
}

@Component({
  selector: 'app-workflow-run-page',
  standalone: true,
  imports: [ReactiveFormsModule, LoadingSkeletonComponent],
  templateUrl: './workflow-run-page.component.html',
  styleUrl: './workflow-run-page.component.css',
})
export class WorkflowRunPageComponent implements OnInit {
  private readonly api = inject(WorkflowApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly fb = inject(FormBuilder);
  private readonly toast = inject(ToastService);
  private readonly confirm = inject(ConfirmService);

  readonly loading = signal(true);
  readonly apiConnected = signal(true);
  readonly form = signal<FormGroup | null>(null);
  readonly isSubmitting = signal(false);
  readonly workflow = signal<WorkflowDetail | null>(null);
  readonly error = signal<string | null>(null);

  readonly fieldSections: FieldSection[] = [
    { title: 'Crawl Configuration', icon: 'fa-spider', keys: ['seed_url', 'max_pages', 'max_depth', 'timeout_seconds'] },
    { title: 'Chunking Settings', icon: 'fa-scissors', keys: ['max_tokens', 'overlap_tokens', 'chunking_methods'] },
    { title: 'Filtering', icon: 'fa-filter', keys: ['allowed_domains', 'allowed_path_prefixes', 'query_terms'] },
    { title: 'Options', icon: 'fa-sliders', keys: ['fetch_again'] },
  ];

  ngOnInit(): void {
    this.route.queryParamMap.pipe(
      switchMap(params => {
        const selector = params.get('workflow') || 'ingest/AWSBedrock';
        return this.api.getWorkflowDetail(selector).pipe(
          tap(wf => {
            this.apiConnected.set(true);
            this.error.set(null);
            this.workflow.set(wf);
            this.form.set(this.buildForm(wf.fields));
            this.loading.set(false);
          }),
          catchError(err => {
            const detail = err?.error?.detail;
            const fallback = FALLBACK_WORKFLOW_DETAILS['ingest/AWSBedrock'];
            this.apiConnected.set(false);
            this.error.set(detail ?? 'API unavailable — using fallback metadata.');
            this.workflow.set(fallback);
            this.form.set(this.buildForm(fallback.fields));
            this.loading.set(false);
            return of(fallback);
          }),
        );
      }),
    ).subscribe();
  }

  getFieldsForSection(section: FieldSection): WorkflowFieldSchema[] {
    const wf = this.workflow();
    if (!wf) return [];
    return section.keys
      .map(key => wf.fields.find(f => f.key === key))
      .filter((f): f is WorkflowFieldSchema => !!f);
  }

  getUnsectionedFields(): WorkflowFieldSchema[] {
    const wf = this.workflow();
    if (!wf) return [];
    const allKeys = this.fieldSections.flatMap(s => s.keys);
    return wf.fields.filter(f => !allKeys.includes(f.key));
  }

  optionsFor(field: WorkflowFieldSchema): WorkflowFieldOption[] {
    return field.options ?? [];
  }

  inputType(field: WorkflowFieldSchema): string {
    if (field.type === 'number') return 'number';
    if (field.type === 'url') return 'url';
    return 'text';
  }

  isInvalid(key: string): boolean {
    const ctrl = this.form()?.get(key);
    return !!(ctrl && ctrl.invalid && ctrl.touched);
  }

  async submit(): Promise<void> {
    const wf = this.workflow();
    const formGroup = this.form();
    if (!wf || !formGroup) return;

    if (formGroup.invalid) {
      formGroup.markAllAsTouched();
      return;
    }

    if (!this.apiConnected()) {
      this.toast.error('API Unavailable', 'Start the backend before submitting.');
      return;
    }

    const confirmed = await this.confirm.confirm({
      title: 'Run Workflow',
      message: `You are about to run "${wf.title || wf.display_name}". This will start a new execution. Continue?`,
      confirmLabel: 'Run',
      variant: 'primary',
    });
    if (!confirmed) return;

    const payload: Record<string, unknown> = {};
    for (const field of wf.fields) {
      const value = formGroup.get(field.key)?.value;
      if (field.type === 'textarea-list') {
        payload[field.key] = String(value || '')
          .split('\n')
          .map(s => s.trim())
          .filter(s => s.length > 0);
      } else if (field.type === 'multiselect') {
        payload[field.key] = Array.isArray(value) ? value : [];
      } else {
        payload[field.key] = value;
      }
    }

    this.isSubmitting.set(true);
    this.error.set(null);

    this.api.runIngestWorkflow(wf.workflow_selector, payload).subscribe({
      next: response => {
        this.isSubmitting.set(false);
        this.toast.success('Execution Started', `Workflow "${wf.display_name}" has been submitted.`);
        this.router.navigate(['/ingest/executions', response.execution_id]);
      },
      error: err => {
        const detail = err?.error?.detail ?? 'Failed to submit workflow run.';
        this.error.set(detail);
        this.toast.error('Submission Failed', detail);
        this.isSubmitting.set(false);
      },
    });
  }

  resetForm(): void {
    const wf = this.workflow();
    if (wf) {
      this.form.set(this.buildForm(wf.fields));
    }
  }

  private buildForm(fields: WorkflowFieldSchema[]): FormGroup {
    const controls: Record<string, FormControl> = {};
    fields.forEach(field => {
      const validators = [];
      if (field.required) validators.push(Validators.required);
      if (field.type === 'number') {
        if (field.min !== undefined) validators.push(Validators.min(field.min));
        if (field.max !== undefined) validators.push(Validators.max(field.max));
      }
      let defaultValue: unknown = field.default;
      if (field.type === 'textarea-list' && Array.isArray(defaultValue)) {
        defaultValue = defaultValue.join('\n');
      }
      controls[field.key] = this.fb.control(defaultValue ?? '', validators);
    });
    return this.fb.group(controls);
  }
}
