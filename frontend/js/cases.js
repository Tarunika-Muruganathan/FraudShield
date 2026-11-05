/**
 * FraudShield - Case Management & Case Details Module
 * Handles case listing, searching, filtering, creation, status updating, and dossier views.
 */

import { API } from './api.js';
import { loadCaseEvidence } from './evidence.js';
import { loadCaseVerification, runCaseVerificationAction } from './verification.js';

let allCasesCache = [];
let currentFilter = {
  search: '',
  status: 'all',
  disputeType: 'all'
};

export function initCasesModule(cases, onSelectCase, onCasesChanged) {
  allCasesCache = cases;
  setupFilters(onSelectCase, onCasesChanged);
  renderCasesTable(filterCases(allCasesCache), onSelectCase, onCasesChanged);
}

export function updateCasesCache(cases, onSelectCase, onCasesChanged) {
  allCasesCache = cases;
  renderCasesTable(filterCases(allCasesCache), onSelectCase, onCasesChanged);
}

function setupFilters(onSelectCase, onCasesChanged) {
  const searchInput = document.getElementById('case-search-input');
  const statusFilter = document.getElementById('case-status-filter');
  const disputeFilter = document.getElementById('case-dispute-filter');
  const resetBtn = document.getElementById('btn-reset-filters');

  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      currentFilter.search = e.target.value.trim().toLowerCase();
      renderCasesTable(filterCases(allCasesCache), onSelectCase, onCasesChanged);
    });
  }

  if (statusFilter) {
    statusFilter.addEventListener('change', (e) => {
      currentFilter.status = e.target.value;
      renderCasesTable(filterCases(allCasesCache), onSelectCase, onCasesChanged);
    });
  }

  if (disputeFilter) {
    disputeFilter.addEventListener('change', (e) => {
      currentFilter.disputeType = e.target.value;
      renderCasesTable(filterCases(allCasesCache), onSelectCase, onCasesChanged);
    });
  }

  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      currentFilter = { search: '', status: 'all', disputeType: 'all' };
      if (searchInput) searchInput.value = '';
      if (statusFilter) statusFilter.value = 'all';
      if (disputeFilter) disputeFilter.value = 'all';
      renderCasesTable(filterCases(allCasesCache), onSelectCase, onCasesChanged);
    });
  }
}

function filterCases(cases) {
  return cases.filter(c => {
    // Search filter across Order ID, Customer, Seller, Transaction, and Description
    const matchesSearch =
      !currentFilter.search ||
      (c.order_id && c.order_id.toLowerCase().includes(currentFilter.search)) ||
      (c.customer_name && c.customer_name.toLowerCase().includes(currentFilter.search)) ||
      (c.seller_name && c.seller_name.toLowerCase().includes(currentFilter.search)) ||
      (c.transaction_id && c.transaction_id.toLowerCase().includes(currentFilter.search)) ||
      (c.description && c.description.toLowerCase().includes(currentFilter.search));

    // Status filter
    const matchesStatus = currentFilter.status === 'all' || c.status === currentFilter.status;

    // Dispute Type filter
    const matchesDispute = currentFilter.disputeType === 'all' || c.dispute_type === currentFilter.disputeType;

    return matchesSearch && matchesStatus && matchesDispute;
  });
}

function renderCasesTable(filteredCases, onSelectCase, onCasesChanged) {
  const container = document.getElementById('cases-table-container');
  const countBadge = document.getElementById('cases-count-badge');

  if (countBadge) {
    countBadge.textContent = `${filteredCases.length} of ${allCasesCache.length} cases`;
  }

  if (!container) return;

  if (allCasesCache.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M20.25 14.15v4.25c0 1.094-.787 2.036-1.872 2.18-2.087.277-4.216.42-6.378.42s-4.291-.143-6.378-.42c-1.085-.144-1.872-1.086-1.872-2.18v-4.25m16.5 0a2.18 2.18 0 00.75-1.661V6a2.25 2.25 0 00-2.25-2.25H5.25A2.25 2.25 0 003 6v6.489c0 .638.283 1.238.75 1.661m16.5 0a48.88 48.88 0 01-16.5 0"/>
        </svg>
        <p class="empty-title">No Investigation Cases Recorded</p>
        <p class="empty-desc">Get started by creating a new dispute case.</p>
        <button class="btn btn-primary btn-sm" id="btn-create-first-case">
          <svg class="btn-icon" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd"/>
          </svg>
          New Investigation
        </button>
      </div>
    `;
    const btnCreate = container.querySelector('#btn-create-first-case');
    if (btnCreate) {
      btnCreate.addEventListener('click', () => {
        document.dispatchEvent(new CustomEvent('open-new-case-modal'));
      });
    }
    return;
  }

  if (filteredCases.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"/>
        </svg>
        <p class="empty-title">No Matching Cases Found</p>
        <p class="empty-desc">Try clearing your search terms or relaxing status filters.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = `
    <table class="data-table">
      <thead>
        <tr>
          <th>Order ID</th>
          <th>Customer</th>
          <th>Seller</th>
          <th>Transaction ID</th>
          <th>Dispute Type</th>
          <th>Status</th>
          <th>Created</th>
          <th class="text-right">Actions</th>
        </tr>
      </thead>
      <tbody>
        ${filteredCases
          .map(
            c => `
          <tr class="table-row-clickable" data-case-id="${c.case_id}">
            <td><span class="font-mono text-cyan">${escapeHtml(c.order_id)}</span></td>
            <td><strong>${escapeHtml(c.customer_name)}</strong></td>
            <td class="text-muted">${escapeHtml(c.seller_name)}</td>
            <td><span class="font-mono text-sm">${c.transaction_id ? escapeHtml(c.transaction_id) : '—'}</span></td>
            <td><span class="badge badge-outline">${formatDisputeType(c.dispute_type)}</span></td>
            <td><span class="badge badge-${c.status}">${formatStatus(c.status)}</span></td>
            <td class="text-muted text-sm">${formatDate(c.created_at)}</td>
            <td class="text-right table-actions" onclick="event.stopPropagation()">
              <button class="btn btn-ghost btn-xs btn-open-case" data-case-id="${c.case_id}" title="Open case dossier">
                Open
              </button>
              <button class="btn btn-ghost-danger btn-xs btn-delete-case-row" data-case-id="${c.case_id}" data-order-id="${escapeHtml(c.order_id)}" title="Delete case">
                <svg class="action-icon text-danger" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd"/>
                </svg>
              </button>
            </td>
          </tr>
        `
          )
          .join('')}
      </tbody>
    </table>
  `;

  // Row and button click handlers
  container.querySelectorAll('.table-row-clickable, .btn-open-case').forEach(el => {
    el.addEventListener('click', () => {
      const caseId = el.getAttribute('data-case-id');
      if (caseId) onSelectCase(caseId);
    });
  });

  container.querySelectorAll('.btn-delete-case-row').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const caseId = btn.getAttribute('data-case-id');
      const orderId = btn.getAttribute('data-order-id');

      document.dispatchEvent(new CustomEvent('open-confirm-modal', {
        detail: {
          title: 'Delete Investigation Case',
          message: `Are you sure you want to permanently delete case for Order '${orderId}'? This will permanently delete the case and purge all associated evidence records and physical files from storage.`,
          confirmText: 'Delete Case & Evidence',
          isDestructive: true,
          onConfirm: async () => {
            try {
              await API.deleteCase(caseId);
              document.dispatchEvent(new CustomEvent('show-toast', {
                detail: { message: `Case ${orderId} successfully deleted.`, type: 'info' }
              }));
              if (onCasesChanged) onCasesChanged();
            } catch (err) {
              document.dispatchEvent(new CustomEvent('show-toast', {
                detail: { message: `Failed to delete case: ${err.message}`, type: 'error' }
              }));
            }
          }
        }
      }));
    });
  });
}

/**
 * Render Case Details View (Dossier + Evidence Locker)
 */
export async function renderCaseDetail(caseId, containerEl, onBack, onCasesChanged) {
  containerEl.innerHTML = `
    <div class="case-detail-header-bar">
      <button class="btn btn-ghost btn-sm" id="btn-back-to-cases">
        &larr; Back to Case List
      </button>
      <div class="header-actions">
        <button class="btn btn-primary btn-sm" id="btn-run-verification">
          <svg class="btn-icon" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
          </svg>
          Run Fraud Verification
        </button>
        <button class="btn btn-danger btn-sm" id="btn-delete-detail-case">
          <svg class="btn-icon" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd"/>
          </svg>
          Delete Case
        </button>
      </div>
    </div>
    <div id="case-detail-content" class="case-detail-grid">
      <div class="skeleton-line" style="height: 300px;"></div>
      <div class="skeleton-line" style="height: 300px;"></div>
    </div>
    <div id="case-verification-wrapper" style="margin-top: 24px;"></div>
  `;

  const btnBack = containerEl.querySelector('#btn-back-to-cases');
  if (btnBack) btnBack.addEventListener('click', onBack);

  try {
    const caseData = await API.getCase(caseId);

    // Setup delete button
    const btnDelete = containerEl.querySelector('#btn-delete-detail-case');
    if (btnDelete) {
      btnDelete.addEventListener('click', () => {
        document.dispatchEvent(new CustomEvent('open-confirm-modal', {
          detail: {
            title: 'Delete Investigation Case',
            message: `Permanently delete case for Order '${caseData.order_id}'? All associated evidence files will be purged from the server disk.`,
            confirmText: 'Delete Everything',
            isDestructive: true,
            onConfirm: async () => {
              try {
                await API.deleteCase(caseId);
                document.dispatchEvent(new CustomEvent('show-toast', {
                  detail: { message: `Case ${caseData.order_id} deleted.`, type: 'info' }
                }));
                onBack();
                if (onCasesChanged) onCasesChanged();
              } catch (err) {
                document.dispatchEvent(new CustomEvent('show-toast', {
                  detail: { message: `Error deleting case: ${err.message}`, type: 'error' }
                }));
              }
            }
          }
        }));
      });
    }

    const contentEl = containerEl.querySelector('#case-detail-content');
    contentEl.innerHTML = `
      <!-- Column 1: Case Dossier -->
      <div class="dossier-card">
        <div class="dossier-header">
          <div>
            <div class="text-xs uppercase tracking-wider text-muted font-mono">Case Dossier</div>
            <h2 class="dossier-title font-mono text-cyan">${escapeHtml(caseData.order_id)}</h2>
          </div>
          <div class="status-selector-wrap">
            <label for="detail-status-select" class="text-xs text-muted">Status:</label>
            <select id="detail-status-select" class="select select-sm select-status-${caseData.status}">
              <option value="pending" ${caseData.status === 'pending' ? 'selected' : ''}>Pending</option>
              <option value="investigating" ${caseData.status === 'investigating' ? 'selected' : ''}>Investigating</option>
              <option value="resolved" ${caseData.status === 'resolved' ? 'selected' : ''}>Resolved</option>
              <option value="rejected" ${caseData.status === 'rejected' ? 'selected' : ''}>Rejected</option>
            </select>
          </div>
        </div>

        <div class="dossier-body">
          <div class="dossier-grid">
            <div class="dossier-field">
              <span class="field-label">Customer Name</span>
              <span class="field-value">${escapeHtml(caseData.customer_name)}</span>
            </div>
            <div class="dossier-field">
              <span class="field-label">Seller Name</span>
              <span class="field-value">${escapeHtml(caseData.seller_name)}</span>
            </div>
            <div class="dossier-field">
              <span class="field-label">Transaction ID</span>
              <span class="field-value font-mono">${caseData.transaction_id ? escapeHtml(caseData.transaction_id) : '<span class="text-muted">Not specified</span>'}</span>
            </div>
            <div class="dossier-field">
              <span class="field-label">Dispute Type</span>
              <span class="field-value"><span class="badge badge-outline">${formatDisputeType(caseData.dispute_type)}</span></span>
            </div>
          </div>

          <div class="dossier-description-box">
            <span class="field-label">Dispute Description & Claims</span>
            <p class="description-text">${escapeHtml(caseData.description)}</p>
          </div>

          <div class="dossier-footer">
            <div class="dossier-timestamps">
              <div class="text-xs text-muted">Case ID: <span class="font-mono text-xs">${caseData.case_id}</span></div>
              <div class="text-xs text-muted">Registered: ${formatDate(caseData.created_at)} &bull; Last Updated: ${formatDate(caseData.updated_at)}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Column 2: Evidence Locker -->
      <div class="evidence-locker-wrapper" id="evidence-locker-container">
        <!-- Injected by evidence.js -->
      </div>
    `;

    // Handle Status Change
    const statusSelect = contentEl.querySelector('#detail-status-select');
    if (statusSelect) {
      statusSelect.addEventListener('change', async (e) => {
        const newStatus = e.target.value;
        const prevStatus = caseData.status;
        statusSelect.disabled = true;

        try {
          const updated = await API.updateCase(caseId, { status: newStatus });
          caseData.status = updated.status;
          caseData.updated_at = updated.updated_at;
          statusSelect.className = `select select-sm select-status-${updated.status}`;
          document.dispatchEvent(new CustomEvent('show-toast', {
            detail: { message: `Case status changed to '${formatStatus(updated.status)}'.`, type: 'success' }
          }));
          if (onCasesChanged) onCasesChanged();
        } catch (err) {
          statusSelect.value = prevStatus;
          document.dispatchEvent(new CustomEvent('show-toast', {
            detail: { message: `Failed to update status: ${err.message}`, type: 'error' }
          }));
        } finally {
          statusSelect.disabled = false;
        }
      });
    }

    // Load Evidence Section
    const evidenceContainer = contentEl.querySelector('#evidence-locker-container');
    if (evidenceContainer) {
      await loadCaseEvidence(caseId, evidenceContainer, () => {
        if (onCasesChanged) onCasesChanged();
        // Refresh verification audit if evidence changed
        const verWrapper = containerEl.querySelector('#case-verification-wrapper');
        if (verWrapper) loadCaseVerification(caseId, verWrapper);
      });
    }

    // Load Fraud Verification Audit Panel
    const verWrapper = containerEl.querySelector('#case-verification-wrapper');
    const btnRunVer = containerEl.querySelector('#btn-run-verification');
    if (btnRunVer && verWrapper) {
      btnRunVer.addEventListener('click', () => {
        runCaseVerificationAction(caseId, verWrapper, btnRunVer);
      });
    }
    if (verWrapper) {
      await loadCaseVerification(caseId, verWrapper);
    }
  } catch (err) {
    containerEl.innerHTML = `
      <div class="case-detail-header-bar">
        <button class="btn btn-ghost btn-sm" id="btn-back-to-cases-error">
          &larr; Back to Case List
        </button>
      </div>
      <div class="alert alert-danger" style="margin-top: 20px;">
        Failed to load case dossier: ${escapeHtml(err.message)}
      </div>
    `;
    const backBtn = containerEl.querySelector('#btn-back-to-cases-error');
    if (backBtn) backBtn.addEventListener('click', onBack);
  }
}

/**
 * Setup "Create New Case" Modal Logic
 */
export function setupNewCaseModal(onCaseCreated) {
  const form = document.getElementById('new-case-form');
  const errorBanner = document.getElementById('new-case-error');
  const submitBtn = document.getElementById('btn-submit-new-case');

  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    errorBanner.classList.add('hidden');
    errorBanner.textContent = '';

    const customerName = form['customer_name'].value.trim();
    const sellerName = form['seller_name'].value.trim();
    const orderId = form['order_id'].value.trim();
    const transactionId = form['transaction_id'].value.trim();
    const disputeType = form['dispute_type'].value;
    const description = form['description'].value.trim();

    // Client-side validations
    if (customerName.length < 2 || customerName.length > 100) {
      showFormError('Customer name must be between 2 and 100 characters.');
      return;
    }
    if (sellerName.length < 2 || sellerName.length > 100) {
      showFormError('Seller name must be between 2 and 100 characters.');
      return;
    }
    if (orderId.length < 2 || orderId.length > 100) {
      showFormError('Order ID must be between 2 and 100 characters.');
      return;
    }
    if (description.length < 10 || description.length > 2000) {
      showFormError('Description must be at least 10 characters and at most 2000 characters.');
      return;
    }

    const payload = {
      customer_name: customerName,
      seller_name: sellerName,
      order_id: orderId,
      dispute_type: disputeType,
      description: description
    };
    if (transactionId) {
      payload.transaction_id = transactionId;
    }

    // Prevent duplicate submission
    submitBtn.disabled = true;
    submitBtn.innerHTML = `
      <span class="spinner-sm"></span> Creating Case...
    `;

    try {
      const createdCase = await API.createCase(payload);
      form.reset();
      document.dispatchEvent(new CustomEvent('close-modal', { detail: { modalId: 'modal-new-case' } }));
      document.dispatchEvent(new CustomEvent('show-toast', {
        detail: { message: `Case for Order '${createdCase.order_id}' created successfully.`, type: 'success' }
      }));
      if (onCaseCreated) onCaseCreated(createdCase.case_id);
    } catch (err) {
      showFormError(err.message || 'Failed to create case.');
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = `Create Investigation`;
    }
  });

  function showFormError(msg) {
    errorBanner.textContent = msg;
    errorBanner.classList.remove('hidden');
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

