export function statusClass(status: string): string {
  const normalized = (status || '').toUpperCase();
  if (normalized.includes('COMPLETE')) return 'ih-status ih-status--success';
  if (normalized.includes('IN_PROGRESS')) return 'ih-status ih-status--warning';
  if (normalized.includes('FAILED')) return 'ih-status ih-status--danger';
  return 'ih-status ih-status--neutral';
}

export function statusIcon(status: string): string {
  const normalized = (status || '').toUpperCase();
  if (normalized.includes('COMPLETE')) return 'fa-circle-check';
  if (normalized.includes('IN_PROGRESS')) return 'fa-hourglass-half';
  if (normalized.includes('FAILED')) return 'fa-triangle-exclamation';
  return 'fa-circle-minus';
}

export function statusLabel(status: string): string {
  const normalized = (status || '').toUpperCase();
  if (normalized.includes('COMPLETE')) return 'Completed';
  if (normalized.includes('IN_PROGRESS')) return 'In Progress';
  if (normalized.includes('FAILED')) return 'Failed';
  if (normalized.includes('SKIPPED')) return 'Skipped';
  if (normalized.includes('NEVER')) return 'Never Executed';
  return status || 'Unknown';
}
