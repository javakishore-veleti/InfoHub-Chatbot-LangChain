import { Component } from '@angular/core';

@Component({
  selector: 'app-model-build-page',
  standalone: true,
  template: `
    <section class="content-card">
      <h2 class="page-heading mb-2"><i class="fa-solid fa-hexagon-nodes me-2 text-primary"></i>Model Build</h2>
      <p class="page-subtitle mb-3">Training orchestration and model lifecycle operations are staged for this domain.</p>
      <div class="row g-3">
        <div class="col-md-6">
          <div class="p-3 border rounded-3 h-100 bg-light-subtle">
            <h3 class="h6 fw-bold mb-2">What will live here</h3>
            <ul class="mb-0 text-secondary">
              <li>Training pipeline configuration</li>
              <li>Experiment tracking and comparison</li>
              <li>Model artifact packaging and promotion</li>
            </ul>
          </div>
        </div>
        <div class="col-md-6">
          <div class="p-3 border rounded-3 h-100 bg-white">
            <h3 class="h6 fw-bold mb-2">Current status</h3>
            <p class="mb-0 text-secondary">API and UI scaffolding are in place, ready for phased implementation.</p>
          </div>
        </div>
      </div>
    </section>
  `,
})
export class ModelBuildPageComponent {}



