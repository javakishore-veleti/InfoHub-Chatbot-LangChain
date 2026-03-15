import { Component } from '@angular/core';

@Component({
  selector: 'app-administration-page',
  standalone: true,
  template: `
    <section class="content-card">
      <h2 class="page-heading mb-2"><i class="fa-solid fa-shield-halved me-2 text-primary"></i>Administration</h2>
      <p class="page-subtitle mb-3">Platform governance, access control, and environment management will be centralized here.</p>
      <div class="row g-3">
        <div class="col-md-4">
          <div class="p-3 border rounded-3 h-100 bg-white">
            <div class="fw-semibold mb-1"><i class="fa-solid fa-users-gear me-2 text-primary"></i>Access Control</div>
            <small class="text-secondary">Roles, permissions, and team onboarding workflows.</small>
          </div>
        </div>
        <div class="col-md-4">
          <div class="p-3 border rounded-3 h-100 bg-white">
            <div class="fw-semibold mb-1"><i class="fa-solid fa-sliders me-2 text-primary"></i>Environment Settings</div>
            <small class="text-secondary">Runtime configuration and deployment-level controls.</small>
          </div>
        </div>
        <div class="col-md-4">
          <div class="p-3 border rounded-3 h-100 bg-white">
            <div class="fw-semibold mb-1"><i class="fa-solid fa-chart-line me-2 text-primary"></i>Operations Health</div>
            <small class="text-secondary">Visibility into platform status and policy compliance.</small>
          </div>
        </div>
      </div>
    </section>
  `,
})
export class AdministrationPageComponent {}



