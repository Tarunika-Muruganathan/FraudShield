/**
 * FraudShield - Main Application Orchestrator
 * Coordinates routing, global state, health polling, modals, and toasts.
 */

import { API } from './api.js';
import { renderDashboard } from './dashboard.js';
import { initCasesModule, updateCasesCache, renderCaseDetail, setupNewCaseModal } from './cases.js';

let casesCache = [];
let activeCaseId = null;

document.addEventListener('DOMContentLoaded', async () => {
  setupNavigation();
  setupModalSystem();
  setupToastSystem();
  setupNewCaseModal(handleCaseCreated);

  // Initial health check
  checkBackendHealth();
  setInterval(checkBackendHealth, 30000);

  // Global refresh button
  const btnRefresh = document.getElementById('btn-global-refresh');
  if (btnRefresh) {
    btnRefresh.addEventListener('click', () => refreshAllData(true));
  }

  // Load cases and route
  await refreshAllData();
  handleRoute();
  window.addEventListener('hashchange', handleRoute);
});

async function checkBackendHealth() {
  const pill = document.getElementById('api-status-pill');
  if (!pill) return;

  try {
    const health = await API.checkHealth();
    if (health && health.status === 'healthy') {
      pill.className = 'status-pill status-pill-online';
      pill.innerHTML = `<span class="pulse-dot"></span> API Connected`;
    } else {
      pill.className = 'status-pill status-pill-warning';
      pill.innerHTML = `<span class="pulse-dot"></span> API Degraded`;
    }
  } catch (e) {
    pill.className = 'status-pill status-pill-offline';
    pill.innerHTML = `<span class="pulse-dot"></span> Backend Offline`;
  }
}

async function refreshAllData(showToastNotice = false) {
  const refreshBtn = document.getElementById('btn-global-refresh');
  if (refreshBtn) refreshBtn.classList.add('rotating');

  try {
    casesCache = await API.getCases();
    
    // Update dashboard & cases
    renderDashboard(casesCache, navigateToCase);
    updateCasesCache(casesCache, navigateToCase, refreshAllData);

    if (showToastNotice) {
      showToast('Data refreshed from investigation database.', 'info');
    }
  } catch (err) {
    showToast(`Failed to load cases: ${err.message}`, 'error');
  } finally {
    if (refreshBtn) {
      setTimeout(() => refreshBtn.classList.remove('rotating'), 500);
    }
  }
}

function setupNavigation() {
  const navLinks = document.querySelectorAll('.nav-link[data-view]');
  navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const view = link.getAttribute('data-view');
      window.location.hash = `#${view}`;
    });
  });

  const btnNewCase = document.getElementById('btn-header-new-case');
  if (btnNewCase) {
    btnNewCase.addEventListener('click', () => {
      openModal('modal-new-case');
    });
  }

  document.addEventListener('open-new-case-modal', () => {
    openModal('modal-new-case');
  });
}

function handleRoute() {
  const hash = window.location.hash || '#dashboard';
  const [route, queryString] = hash.split('?');
  const params = new URLSearchParams(queryString || '');

  const viewDashboard = document.getElementById('view-dashboard');
  const viewCases = document.getElementById('view-cases');
  const viewCaseDetail = document.getElementById('view-case-detail');
  const navLinks = document.querySelectorAll('.nav-link[data-view]');

  // Hide all views
  viewDashboard.classList.add('hidden');
  viewCases.classList.add('hidden');
  viewCaseDetail.classList.add('hidden');

  navLinks.forEach(link => link.classList.remove('active'));

  if (route === '#case-detail') {
    const id = params.get('id');
    if (id) {
      activeCaseId = id;
      viewCaseDetail.classList.remove('hidden');
      renderCaseDetail(id, viewCaseDetail, () => {
        window.location.hash = '#cases';
      }, refreshAllData);
    } else {
      window.location.hash = '#cases';
    }
  } else if (route === '#cases') {
    viewCases.classList.remove('hidden');
    const caseLink = document.querySelector('.nav-link[data-view="cases"]');
    if (caseLink) caseLink.classList.add('active');
    initCasesModule(casesCache, navigateToCase, refreshAllData);
  } else {
    // Default: Dashboard
    viewDashboard.classList.remove('hidden');
    const dashLink = document.querySelector('.nav-link[data-view="dashboard"]');
    if (dashLink) dashLink.classList.add('active');
    renderDashboard(casesCache, navigateToCase);
  }
}

function navigateToCase(caseId) {
  window.location.hash = `#case-detail?id=${encodeURIComponent(caseId)}`;
}

async function handleCaseCreated(newCaseId) {
  await refreshAllData();
  navigateToCase(newCaseId);
}

// Modal System
function setupModalSystem() {
  document.querySelectorAll('.modal-backdrop, .modal-close').forEach(el => {
    el.addEventListener('click', (e) => {
      if (e.target.classList.contains('modal-backdrop') || e.target.classList.contains('modal-close')) {
        const modal = e.target.closest('.modal');
        if (modal) closeModal(modal.id);
      }
    });
  });

  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal:not(.hidden)').forEach(m => closeModal(m.id));
    }
  });

  document.addEventListener('open-confirm-modal', (e) => {
    const { title, message, confirmText, isDestructive, onConfirm } = e.detail;
    const modal = document.getElementById('modal-confirm');
    if (!modal) return;

    modal.querySelector('#confirm-modal-title').textContent = title || 'Confirm Action';
    modal.querySelector('#confirm-modal-message').textContent = message || 'Are you sure?';
    
    const confirmBtn = modal.querySelector('#confirm-modal-btn-confirm');
    confirmBtn.textContent = confirmText || 'Confirm';
    confirmBtn.className = isDestructive ? 'btn btn-danger' : 'btn btn-primary';

    // Replace click handler cleanly
    const newBtn = confirmBtn.cloneNode(true);
    confirmBtn.parentNode.replaceChild(newBtn, confirmBtn);

    newBtn.addEventListener('click', async () => {
      closeModal('modal-confirm');
      if (onConfirm) await onConfirm();
    });

    openModal('modal-confirm');
  });

  document.addEventListener('close-modal', (e) => {
    if (e.detail && e.detail.modalId) {
      closeModal(e.detail.modalId);
    }
  });
}

function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('hidden');
    document.body.classList.add('modal-open');
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('hidden');
    document.body.classList.remove('modal-open');
  }
}

// Toast System
function setupToastSystem() {
  document.addEventListener('show-toast', (e) => {
    const { message, type = 'info', duration = 4000 } = e.detail;
    showToast(message, type, duration);
  });
}

function showToast(message, type = 'info', duration = 4000) {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  
  let iconSvg = '';
  if (type === 'success') {
    iconSvg = `<svg class="toast-icon text-success" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg>`;
  } else if (type === 'error') {
    iconSvg = `<svg class="toast-icon text-danger" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/></svg>`;
  } else {
    iconSvg = `<svg class="toast-icon text-cyan" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/></svg>`;
  }

  toast.innerHTML = `
    ${iconSvg}
    <div class="toast-message">${escapeHtml(message)}</div>
    <button class="toast-close" title="Dismiss">&times;</button>
  `;

  toast.querySelector('.toast-close').addEventListener('click', () => {
    toast.remove();
  });

  container.appendChild(toast);

  setTimeout(() => {
    toast.classList.add('toast-fadeout');
    setTimeout(() => toast.remove(), 300);
  }, duration);
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
