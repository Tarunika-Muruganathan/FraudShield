/**
 * FraudShield - Automated Investigation Timeline UI Module
 * Renders an append-only chronological history of case events, document processing,
 * verification runs, and AI investigation steps with category filtering, sorting, and metadata inspection.
 */

import { API } from './api.js';

let activeCategoryFilter = null;
let activeSortOrder = 'desc';

function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function formatLocalTime(isoString) {
  if (!isoString) return '<span class="text-muted">Timestamp unrecorded</span>';
  try {
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return '<span class="text-muted">Invalid timestamp</span>';
    return d.toLocaleString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      timeZoneName: 'short',
    });
  } catch (err) {
    return escapeHtml(isoString);
  }
}

function getCategoryBadge(category) {
  switch ((category || '').toLowerCase()) {
    case 'case':
      return '<span class="timeline-badge badge-case">Case Dossier</span>';
    case 'evidence':
      return '<span class="timeline-badge badge-evidence">Evidence</span>';
    case 'ocr':
      return '<span class="timeline-badge badge-ocr">OCR & Extraction</span>';
    case 'verification':
      return '<span class="timeline-badge badge-verification">Verification</span>';
    case 'investigation':
      return '<span class="timeline-badge badge-investigation">AI Investigation</span>';
    case 'human_review':
      return '<span class="timeline-badge badge-review">Human Review</span>';
    default:
      return `<span class="timeline-badge badge-case">${escapeHtml(category)}</span>`;
  }
}

function getActorBadge(actor) {
  if (!actor) return '';
  switch (actor.toLowerCase()) {
    case 'investigator':
      return '<span class="actor-badge actor-human">Investigator</span>';
    case 'ocr_engine':
      return '<span class="actor-badge actor-system">OCR Engine</span>';
    case 'verification_engine':
      return '<span class="actor-badge actor-rule">Rule Engine</span>';
    case 'ai_agent':
      return '<span class="actor-badge actor-ai">AI Agent</span>';
    default:
      return `<span class="actor-badge actor-system">${escapeHtml(actor)}</span>`;
  }
}

export async function loadCaseTimeline(caseId, containerEl) {
  if (!containerEl) return;

  containerEl.innerHTML = `
    <div class="card timeline-card">
      <div class="card-header flex-between">
        <div>
          <div class="badge badge-outline" style="border-color: rgba(6,182,212,0.5); color: #06b6d4; margin-bottom: 6px;">
            Audit Ledger
          </div>
          <h3 class="card-title">Automated Investigation Timeline</h3>
          <p class="card-subtitle">Chronological ledger of case actions, document uploads, OCR events, verification results, and AI queries</p>
        </div>
        <div class="timeline-header-actions">
          <div class="btn-group btn-group-sm">
            <button class="btn btn-ghost btn-sm ${activeSortOrder === 'desc' ? 'btn-active' : ''}" id="timeline-sort-desc" title="Newest events first">
              Newest First &darr;
            </button>
            <button class="btn btn-ghost btn-sm ${activeSortOrder === 'asc' ? 'btn-active' : ''}" id="timeline-sort-asc" title="Oldest events first">
              Oldest First &uarr;
            </button>
          </div>
        </div>
      </div>

      <!-- Category Filter Pills -->
      <div class="timeline-filters-bar">
        <span class="text-xs text-muted font-mono" style="margin-right: 8px;">FILTER:</span>
        <button class="filter-pill ${activeCategoryFilter === null ? 'active' : ''}" data-cat="">All Events</button>
        <button class="filter-pill ${activeCategoryFilter === 'case' ? 'active' : ''}" data-cat="case">Case Lifecycle</button>
        <button class="filter-pill ${activeCategoryFilter === 'evidence' ? 'active' : ''}" data-cat="evidence">Evidence</button>
        <button class="filter-pill ${activeCategoryFilter === 'ocr' ? 'active' : ''}" data-cat="ocr">OCR</button>
        <button class="filter-pill ${activeCategoryFilter === 'verification' ? 'active' : ''}" data-cat="verification">Verification</button>
        <button class="filter-pill ${activeCategoryFilter === 'investigation' ? 'active' : ''}" data-cat="investigation">AI Agent</button>
      </div>

      <div class="card-body" id="timeline-events-content">
        <div class="skeleton-list">
          <div class="skeleton-line" style="height: 60px; margin-bottom: 12px;"></div>
          <div class="skeleton-line" style="height: 60px; margin-bottom: 12px;"></div>
          <div class="skeleton-line" style="height: 60px;"></div>
        </div>
      </div>
    </div>
  `;

  // Hook Sorting Buttons
  const btnSortDesc = containerEl.querySelector('#timeline-sort-desc');
  const btnSortAsc = containerEl.querySelector('#timeline-sort-asc');

  if (btnSortDesc) {
    btnSortDesc.addEventListener('click', () => {
      if (activeSortOrder !== 'desc') {
        activeSortOrder = 'desc';
        loadCaseTimeline(caseId, containerEl);
      }
    });
  }
  if (btnSortAsc) {
    btnSortAsc.addEventListener('click', () => {
      if (activeSortOrder !== 'asc') {
        activeSortOrder = 'asc';
        loadCaseTimeline(caseId, containerEl);
      }
    });
  }

  // Hook Category Filter Pills
  const filterPills = containerEl.querySelectorAll('.filter-pill');
  filterPills.forEach((pill) => {
    pill.addEventListener('click', () => {
      const cat = pill.getAttribute('data-cat') || null;
      activeCategoryFilter = cat;
      loadCaseTimeline(caseId, containerEl);
    });
  });

  const contentEl = containerEl.querySelector('#timeline-events-content');

  try {
    const events = await API.getCaseTimeline(caseId, {
      category: activeCategoryFilter,
      sort: activeSortOrder,
      limit: 100,
    });

    if (!events || events.length === 0) {
      contentEl.innerHTML = `
        <div class="timeline-empty-state">
          <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div class="empty-title">No Timeline Events Recorded</div>
          <p class="empty-desc">
            ${activeCategoryFilter ? `No events recorded in the '${activeCategoryFilter}' category.` : 'Case has no recorded audit events yet.'}
          </p>
        </div>
      `;
      return;
    }

    renderTimelineEvents(events, contentEl);
  } catch (err) {
    contentEl.innerHTML = `
      <div class="alert alert-danger">
        <strong>Error loading investigation timeline:</strong> ${escapeHtml(err.message)}
      </div>
    `;
  }
}

function renderTimelineEvents(events, containerEl) {
  let html = `<div class="timeline-spine">`;

  events.forEach((ev, idx) => {
    const hasMetadata = ev.metadata && Object.keys(ev.metadata).length > 0;
    const metadataDrawerId = `meta-drawer-${ev.event_id}`;

    let relatedLinksHtml = '';
    if (ev.related_evidence_ids && ev.related_evidence_ids.length > 0) {
      relatedLinksHtml += ev.related_evidence_ids
        .map(id => `<span class="chip chip-mono" title="Evidence ID: ${escapeHtml(id)}">Doc: ${escapeHtml(id.slice(0, 8))}...</span>`)
        .join(' ');
    }
    if (ev.related_verification_id) {
      relatedLinksHtml += ` <span class="chip chip-mono" title="Verification ID: ${escapeHtml(ev.related_verification_id)}">Verification: ${escapeHtml(ev.related_verification_id.slice(0, 8))}...</span>`;
    }
    if (ev.related_investigation_id) {
      relatedLinksHtml += ` <span class="chip chip-mono" title="Investigation ID: ${escapeHtml(ev.related_investigation_id)}">AI Run: ${escapeHtml(ev.related_investigation_id.slice(0, 8))}...</span>`;
    }

    let metaTableHtml = '';
    if (hasMetadata) {
      metaTableHtml = `
        <div class="timeline-meta-drawer hidden" id="${metadataDrawerId}">
          <div class="timeline-meta-grid">
            ${Object.entries(ev.metadata)
              .map(([key, val]) => `
                <div class="meta-field">
                  <span class="meta-key">${escapeHtml(key)}:</span>
                  <span class="meta-value font-mono">${escapeHtml(typeof val === 'object' ? JSON.stringify(val) : String(val))}</span>
                </div>
              `).join('')}
          </div>
        </div>
      `;
    }

    html += `
      <div class="timeline-item timeline-item-${escapeHtml(ev.category)}">
        <div class="timeline-marker"></div>
        <div class="timeline-body">
          <div class="timeline-item-header">
            <div class="flex-align-center" style="gap: 8px; flex-wrap: wrap;">
              ${getCategoryBadge(ev.category)}
              <h4 class="timeline-item-title">${escapeHtml(ev.title)}</h4>
              ${getActorBadge(ev.actor)}
            </div>
            <div class="timeline-timestamp font-mono">
              ${formatLocalTime(ev.event_timestamp || ev.recorded_at)}
            </div>
          </div>

          <div class="timeline-item-desc">
            ${escapeHtml(ev.description)}
          </div>

          ${relatedLinksHtml ? `<div class="timeline-related-row">${relatedLinksHtml}</div>` : ''}

          ${hasMetadata ? `
            <button class="btn btn-ghost btn-xs timeline-toggle-meta" data-target="${metadataDrawerId}">
              <span>View Audit Metadata</span> &darr;
            </button>
            ${metaTableHtml}
          ` : ''}
        </div>
      </div>
    `;
  });

  html += `</div>`;
  containerEl.innerHTML = html;

  // Setup metadata toggle buttons
  containerEl.querySelectorAll('.timeline-toggle-meta').forEach((btn) => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-target');
      const drawer = containerEl.querySelector(`#${targetId}`);
      if (drawer) {
        const isHidden = drawer.classList.contains('hidden');
        drawer.classList.toggle('hidden', !isHidden);
        btn.querySelector('span').textContent = isHidden ? 'Hide Audit Metadata' : 'View Audit Metadata';
        btn.innerHTML = isHidden
          ? '<span>Hide Audit Metadata</span> &uarr;'
          : '<span>View Audit Metadata</span> &darr;';
      }
    });
  });
}

