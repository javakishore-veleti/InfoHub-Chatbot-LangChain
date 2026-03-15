import { Component } from '@angular/core';

@Component({
  selector: 'app-home-page',
  standalone: true,
  template: `
    <section class="content-card">
      <div class="row g-3 align-items-stretch">
        <div class="col-xl-7">
          <div class="h-100 p-4 rounded-4 border bg-light-subtle">
            <h2 class="page-heading mb-2"><i class="fa-solid fa-compass me-2 text-primary"></i>Welcome to InfoHub</h2>
            <p class="page-subtitle mb-3">
              Your operations cockpit for workflow orchestration, execution tracking, and platform reliability.
            </p>
            <div class="d-flex flex-wrap gap-2">
              <span class="badge text-bg-primary"><i class="fa-solid fa-inbox me-1"></i>Ingest Operations</span>
              <span class="badge text-bg-secondary"><i class="fa-solid fa-hexagon-nodes me-1"></i>Model Build (next)</span>
              <span class="badge text-bg-dark"><i class="fa-solid fa-shield-halved me-1"></i>Administration (next)</span>
            </div>
          </div>
        </div>
        <div class="col-xl-5">
          <div class="h-100 p-4 rounded-4 border bg-white">
            <h3 class="h5 mb-3">Current Focus</h3>
            <div class="d-flex align-items-start gap-2 mb-3">
              <i class="fa-solid fa-diagram-project text-primary mt-1"></i>
              <div>
                <div class="fw-semibold">Workflow Catalog</div>
                <small class="text-secondary">Browse and start workflows with clear metadata.</small>
              </div>
            </div>
            <div class="d-flex align-items-start gap-2">
              <i class="fa-solid fa-clock-rotate-left text-primary mt-1"></i>
              <div>
                <div class="fw-semibold">Execution Monitoring</div>
                <small class="text-secondary">Filter, inspect status, and trace run folders quickly.</small>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  `,
})
export class HomePageComponent {}



