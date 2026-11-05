/**
 * FraudShield - Deterministic Fraud Verification Audit UI
 * Renders cross-document discrepancy reports, timeline checks, and risk indicators.
 */

import { API } from './api.js';

export async function loadCaseVerification(caseId, containerEl) {
  if (!containerEl) return;

  try {
    const ver = await API.getCaseVerification(caseId);
    renderAuditReport(ver, containerEl, caseId);
  } catch (err) {
    // If 404 (not yet run), render empty audit prompt
    renderEmptyAuditState(containerEl, caseId);
  }
}

export async function runCaseVerificationAction(caseId, containerEl, btnEl) {
  if (btnEl) {
    btnEl.disabled = true;
    btnEl.innerHTML = `<span class="spinner-sm"></span> Auditing Documents...`;
  }

  try {
    const ver = await API.verifyCase(caseId);
    document.dispatchEvent(new CustomEvent('show-toast', {
      detail: {
        message: `Fraud verification audit completed (Risk: ${ver.risk_level}, Score: ${ver.risk_score}/100).`,
        type: ver.risk_level === 'CRITICAL' ? 'warning' : 'success'
      }
    }));
    renderAuditReport(ver, containerEl, caseId);
  } catch (err) {
    document.dispatchEvent(new CustomEvent('show-toast', {
      detail: { message: `Verification failed: ${err.message}`, type: 'error' }
    }));
  } finally {
    if (btnEl) {
      btnEl.disabled = false;
      btnEl.innerHTML = `
        <svg class="btn-icon" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
        </svg>
        Re-Run Verification
      `;
    }
  }
}

function renderEmptyAuditState(containerEl, caseId) {
  containerEl.innerHTML = `
    <div class="verification-audit-panel">
      <div class="audit-header">
        <div class="audit-header-title">
          <span class="text-xs uppercase tracking-wider text-muted font-mono">Fraud Verification Engine</span>
          <h3 class="panel-heading">Document Discrepancy & Timeline Audit</h3>
        </div>
      </div>
      <div class="empty-state empty-state-compact">
        <svg class="empty-icon-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z"/>
        </svg>
        <p class="empty-title">Audit Not Yet Generated</p>
        <p class="empty-desc">Run the Fraud Verification Engine to cross-reconcile payment receipts, invoices, and courier delivery proofs.</p>
        <button class="btn btn-primary btn-sm btn-trigger-audit" style="margin-top: 10px;">
          Execute Verification Audit
        </button>
      </div>
    </div>
  `;

  const btn = containerEl.querySelector('.btn-trigger-audit');
  if (btn) {
    btn.addEventListener('click', () => runCaseVerificationAction(caseId, containerEl, btn));
  }
}

function renderAuditReport(ver, containerEl, caseId) {
  const riskClass = `risk-${ver.risk_level.toLowerCase()}`;
  const badgeClass = getRiskBadgeClass(ver.risk_level);

  const criticals = (ver.discrepancies || []).filter(d => d.severity === 'CRITICAL');
  const warnings = (ver.discrepancies || []).filter(d => d.severity === 'WARNING');
  const infos = (ver.discrepancies || []).filter(d => d.severity === 'INFO');
  const missing = ver.missing_evidence || [];
  const matches = ver.matches || [];

  containerEl.innerHTML = `
    <div class="verification-audit-panel ${riskClass}">
      <div class="audit-header">
        <div class="audit-header-title">
          <div class="text-xs uppercase tracking-wider text-muted font-mono">Fraud Verification Engine &bull; Forensic Report</div>
          <div class="audit-title-row">
            <h3 class="panel-heading">Documentary Inconsistency & Timeline Audit</h3>
            <span class="badge ${badgeClass} font-mono">${ver.risk_level} RISK &bull; SCORE ${ver.risk_score}/100</span>
          </div>
        </div>
        <div class="audit-meta text-xs text-muted">
          Audited: ${formatDateTime(ver.verified_at)}
        </div>
      </div>

      <!-- Impartiality Notice -->
      <div class="audit-disclaimer">
        <svg class="disclaimer-icon" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
        </svg>
        <span>
          <strong>Investigative Notice:</strong> This audit compares documentary claims and extracted metadata across uploaded files.
          Findings indicate documentary consistency and timeline anomalies. They do not constitute an automated or legal determination of fraud.
        </span>
      </div>

      <!-- Executive Summary -->
      <div class="audit-summary-box">
        <p class="summary-text">${escapeHtml(ver.summary)}</p>
      </div>

      <!-- Audit Sections Grid -->
      <div class="audit-findings-grid">
        
        <!-- Column 1: Discrepancies & Anomalies -->
        <div class="audit-column">
          <div class="finding-group-header text-danger">
            <svg class="finding-icon" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
            </svg>
            Critical Documentary Contradictions (${criticals.length})
          </div>

          ${criticals.length === 0 ? `
            <div class="empty-inline-finding text-muted">Zero critical documentary contradictions detected.</div>
          ` : `
            <div class="finding-list">
              ${criticals.map(item => renderFindingCard(item, 'critical')).join('')}
            </div>
          `}

          <!-- Warnings & Missing Proof -->
          <div class="finding-group-header text-warning" style="margin-top: 16px;">
            <svg class="finding-icon" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
            </svg>
            Warnings & Missing Evidence (${warnings.length + missing.length})
          </div>

          ${(warnings.length === 0 && missing.length === 0) ? `
            <div class="empty-inline-finding text-muted">All expected evidence categories and attributes are present.</div>
          ` : `
            <div class="finding-list">
              ${warnings.map(item => renderFindingCard(item, 'warning')).join('')}
              ${missing.map(item => renderMissingEvidenceCard(item)).join('')}
            </div>
          `}
        </div>

        <!-- Column 2: Corroborated Matches & Observations -->
        <div class="audit-column">
          <div class="finding-group-header text-success">
            <svg class="finding-icon" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
            </svg>
            Corroborated Claims (${matches.length})
          </div>

          ${matches.length === 0 ? `
            <div class="empty-inline-finding text-muted">No cross-document corroboration identified yet.</div>
          ` : `
            <div class="finding-list">
              ${matches.map(item => renderMatchCard(item)).join('')}
            </div>
          `}

          ${infos.length > 0 ? `
            <div class="finding-group-header text-cyan" style="margin-top: 16px;">
              <svg class="finding-icon" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
              </svg>
              Investigative Observations (${infos.length})
            </div>
            <div class="finding-list">
              ${infos.map(item => renderFindingCard(item, 'info')).join('')}
            </div>
          ` : ''}
        </div>
      </div>
    </div>
  `;
}

function renderFindingCard(item, type) {
  const evPills = (item.evidence_ids || []).map(id => `
    <span class="evidence-ref-pill font-mono" title="Referenced Evidence ID">${id.substring(0, 8)}...</span>
  `).join('');

  return `
    <div class="finding-card finding-${type}">
      <div class="finding-header">
        <span class="finding-title">${escapeHtml(item.title)}</span>
        <span class="badge badge-sm badge-${type}">${item.domain || item.severity}</span>
      </div>
      <p class="finding-desc">${escapeHtml(item.description)}</p>
      ${evPills ? `<div class="finding-evidence-row"><span class="text-muted text-xs">Linked Evidence:</span> ${evPills}</div>` : ''}
    </div>
  `;
}

function renderMissingEvidenceCard(item) {
  return `
    <div class="finding-card finding-warning">
      <div class="finding-header">
        <span class="finding-title">${escapeHtml(item.title)}</span>
        <span class="badge badge-sm badge-warning">EVIDENCE DEFICIT</span>
      </div>
      <p class="finding-desc">${escapeHtml(item.description)}</p>
    </div>
  `;
}

function renderMatchCard(item) {
  const evPills = (item.evidence_ids || []).map(id => `
    <span class="evidence-ref-pill font-mono" title="Referenced Evidence ID">${id.substring(0, 8)}...</span>
  `).join('');

  return `
    <div class="finding-card finding-match">
      <div class="finding-header">
        <span class="finding-title">${escapeHtml(item.title)}</span>
        <span class="badge badge-sm badge-resolved">${item.domain}</span>
      </div>
      <p class="finding-desc">${escapeHtml(item.description)}</p>
      ${evPills ? `<div class="finding-evidence-row"><span class="text-muted text-xs">Corroborated in:</span> ${evPills}</div>` : ''}
    </div>
  `;
}

function getRiskBadgeClass(level) {
  switch (level) {
    case 'CRITICAL': return 'badge-rejected';
    case 'HIGH': return 'badge-pending';
    case 'MEDIUM': return 'badge-investigating';
    case 'LOW':
    default: return 'badge-resolved';
  }
}

function formatDateTime(isoStr) {
  if (!isoStr) return '—';
  const d = new Date(isoStr);
  return d.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
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

