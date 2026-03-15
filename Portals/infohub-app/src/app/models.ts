export interface WorkflowLastExecutionSummary {
  execution_id?: string | null;
  status: string;
  started_at?: string | null;
  completed_at?: string | null;
}

export interface WorkflowSummary {
  module: string;
  workflow_selector: string;
  workflow_parent: string;
  workflow_child: string;
  workflow_id: string;
  display_name: string;
  short_description: string;
  last_execution: WorkflowLastExecutionSummary;
}

export interface WorkflowFieldOption {
  label: string;
  value: string;
}

export interface WorkflowFieldSchema {
  key: string;
  label: string;
  type: string;
  description?: string;
  help?: string;
  placeholder?: string;
  required?: boolean;
  default?: unknown;
  read_only?: boolean;
  min?: number;
  max?: number;
  pattern?: string;
  options?: WorkflowFieldOption[];
}

export interface WorkflowDetail extends WorkflowSummary {
  title: string;
  description: string;
  fields: WorkflowFieldSchema[];
  raw_config: Record<string, unknown>;
}

export interface ExecutionSummary {
  execution_id: string;
  workflow_selector: string;
  workflow_id: string;
  workflow_parent: string;
  workflow_child: string;
  module_name: string;
  display_name: string;
  status: string;
  return_code?: number | null;
  active_run_folder?: string | null;
  reused_latest_run?: boolean;
  started_at: string;
  completed_at?: string | null;
}

export interface ExecutionDetail extends ExecutionSummary {
  request_payload: Record<string, unknown>;
  effective_config: Record<string, unknown>;
  response_summary: Record<string, unknown>;
  error_message?: string | null;
}

export interface ExecutionPage {
  items: ExecutionSummary[];
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
}

