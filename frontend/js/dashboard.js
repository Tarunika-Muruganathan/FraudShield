/**
 * FraudShield - Dashboard Module
 * Visualizes case metrics, distributions, and recent forensic activities.
 */

export function renderDashboard(cases, onSelectCase) {
  const total = cases.length;
  const pending = cases.filter(c => c.status === 'pending').length;
  const investigating = cases.filter(c => c.status === 'investigating').length;
  const resolved = cases.filter(c => c.status === 'resolved').length;
  const rejected = cases.filter(c => c.status === 'rejected').length;
  const completed = resolved + rejected;

  // Stat Counters
  document.getElementById('stat-total-cases').textContent = total;
  document.getElementById('stat-pending-cases').textContent = pending;
  document.getElementById('stat-investigating-cases').textContent = investigating;
  document.getElementById('stat-completed-cases').textContent = completed;

  // Status Distribution Calculations
  const pendingPct = total ? Math.round((pending / total) * 100) : 0;
  const investigatingPct = total ? Math.round((investigating / total) * 100) : 0;
  const resolvedPct = total ? Math.round((resolved / total) * 100) : 0;
  const rejectedPct = total ? Math.round((rejected / total) * 100) : 0;

  // Render Status Bars
  const statusBar = document.getElementById('dashboard-status-bar');
  if (statusBar) {
    if (total === 0) {
      statusBar.innerHTML = `<div class="status-bar-empty" style="width: 100%">No cases recorded</div>`;
    } else {
      statusBar.innerHTML = `
        <div class="status-segment status-pending" style="width: ${pendingPct}%" title="Pending: ${pending} (${pendingPct}%)"></div>
        <div class="status-segment status-investigating" style="width: ${investigatingPct}%" title="Investigating: ${investigating} (${investigatingPct}%)"></div>
        <div class="status-segment status-resolved" style="width: ${resolvedPct}%" title="Resolved: ${resolved} (${resolvedPct}%)"></div>
        <div class="status-segment status-rejected" style="width: ${rejectedPct}%" title="Rejected: ${rejected} (${rejectedPct}%)"></div>
      `;
    }
  }

  // Render Status Legend
  const statusLegend = document.getElementById('dashboard-status-legend');
  if (statusLegend) {
    statusLegend.innerHTML = `
      <div class="legend-item">
        <span class="legend-dot status-dot-pending"></span>
        <span class="legend-label">Pending</span>
        <span class="legend-value">${pending} <small>(${pendingPct}%)</small></span>
      </div>
      <div class="legend-item">
        <span class="legend-dot status-dot-investigating"></span>
        <span class="legend-label">Investigating</span>
        <span class="legend-value">${investigating} <small>(${investigatingPct}%)</small></span>
      </div>
      <div class="legend-item">
        <span class="legend-dot status-dot-resolved"></span>
        <span class="legend-label">Resolved</span>
        <span class="legend-value">${resolved} <small>(${resolvedPct}%)</small></span>
      </div>
      <div class="legend-item">
        <span class="legend-dot status-dot-rejected"></span>
        <span class="legend-label">Rejected</span>
        <span class="legend-value">${rejected} <small>(${rejectedPct}%)</small></span>
      </div>
    `;
  }

  // Dispute Type Distribution
  const disputeCounts = {
    non_delivery: cases.filter(c => c.dispute_type === 'non_delivery').length,
    fake_delivery: cases.filter(c => c.dispute_type === 'fake_delivery').length,
    payment_fraud: cases.filter(c => c.dispute_type === 'payment_fraud').length,
    amount_mismatch: cases.filter(c => c.dispute_type === 'amount_mismatch').length,
    other: cases.filter(c => c.dispute_type === 'other').length,
  };

  const disputeLabels = {
    non_delivery: 'Non-Delivery',
    fake_delivery: 'Fake Delivery',
    payment_fraud: 'Payment Fraud',
    amount_mismatch: 'Amount Mismatch',
    other: 'Other Discrepancy',
  };

  const disputeContainer = document.getElementById('dashboard-dispute-types');
  if (disputeContainer) {
    if (total === 0) {
      disputeContainer.innerHTML = `<div class="empty-inline-state">No dispute data available</div>`;
    } else {
      disputeContainer.innerHTML = Object.entries(disputeCounts)
        .map(([type, count]) => {
          const pct = total ? Math.round((count / total) * 100) : 0;
          return `
            <div class="dispute-type-row">
              <div class="dispute-type-header">
                <span class="dispute-type-name">${disputeLabels[type]}</span>
                <span class="dispute-type-count">${count} <small class="text-muted">(${pct}%)</small></span>
              </div>
              <div class="progress-track">
                <div class="progress-fill" style="width: ${pct}%"></div>
              </div>
            </div>
          `;
        })
        .join('');
    }
  }

  // Recent Cases List (up to 5 recent)
  const recentCasesContainer = document.getElementById('dashboard-recent-cases');
  if (recentCasesContainer) {
    if (cases.length === 0) {
      recentCasesContainer.innerHTML = `
        <div class="empty-state">
          <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"/>
          </svg>
          <p class="empty-title">No Investigation Cases Yet</p>
          <p class="empty-desc">Create your first dispute case to begin tracking evidence and detecting payment fraud.</p>
          <button class="btn btn-primary btn-sm" id="btn-dashboard-new-case">
            <svg class="btn-icon" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd"/>
            </svg>
            Create First Case
          </button>
        </div>
      `;
      const btnNew = document.getElementById('btn-dashboard-new-case');
      if (btnNew) {
        btnNew.addEventListener('click', () => {
          window.location.hash = '#cases';
          document.dispatchEvent(new CustomEvent('open-new-case-modal'));
        });
      }
    } else {
      const recent = cases.slice(0, 5);
      recentCasesContainer.innerHTML = `
        <table class="data-table">
          <thead>
            <tr>
              <th>Order ID</th>
              <th>Customer</th>
              <th>Seller</th>
              <th>Dispute Type</th>
              <th>Status</th>
              <th>Created</th>
              <th class="text-right">Action</th>
            </tr>
          </thead>
          <tbody>
            ${recent
              .map(
                c => `
              <tr class="table-row-clickable" data-case-id="${c.case_id}">
                <td><span class="font-mono text-cyan">${escapeHtml(c.order_id)}</span></td>
                <td>${escapeHtml(c.customer_name)}</td>
                <td class="text-muted">${escapeHtml(c.seller_name)}</td>
                <td><span class="badge badge-outline">${formatDisputeType(c.dispute_type)}</span></td>
                <td><span class="badge badge-${c.status}">${formatStatus(c.status)}</span></td>
                <td class="text-muted text-sm">${formatDate(c.created_at)}</td>
                <td class="text-right">
                  <button class="btn btn-ghost btn-xs btn-view-case" data-case-id="${c.case_id}">
                    Inspect &rarr;
                  </button>
                </td>
              </tr>
            `
              )
              .join('')}
          </tbody>
        </table>
      `;

      // Event listeners for inspection clicks
      recentCasesContainer.querySelectorAll('.btn-view-case, .table-row-clickable').forEach(el => {
        el.addEventListener('click', (e) => {
          const caseId = el.getAttribute('data-case-id');
          if (caseId) onSelectCase(caseId);
        });
      });
    }
  }
}

function formatDisputeType(type) {
  const map = {
    non_delivery: 'Non-Delivery',
    fake_delivery: 'Fake Delivery',
    payment_fraud: 'Payment Fraud',
    amount_mismatch: 'Amount Mismatch',
    other: 'Other'
  };
  return map[type] || type;
}

function formatStatus(status) {
  const map = {
    pending: 'Pending',
    investigating: 'Investigating',
    resolved: 'Resolved',
    rejected: 'Rejected'
  };
  return map[status] || status;
}

function formatDate(isoString) {
  if (!isoString) return '—';
  const d = new Date(isoString);
  return d.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

