/**
 * FraudShield - AI Investigation Agent UI Component
 * Provides automated forensic case synthesis, evidence-cited observations,
 * prioritized recommended actions, and interactive Q&A chat.
 */

import { API } from './api.js';

export async function loadCaseInvestigation(caseId, containerEl) {
  if (!containerEl) return;

  try {
    const inv = await API.getLatestInvestigation(caseId);
    renderInvestigationReport(inv, containerEl, caseId);
  } catch (err) {
    // If 404 (not yet analyzed), render empty state
    renderEmptyInvestigationState(containerEl, caseId);
  }
}

export async function startInvestigationAction(caseId, containerEl, triggerBtn) {
  if (triggerBtn) {
    triggerBtn.disabled = true;
    triggerBtn.innerHTML = `<span class="spinner-sm"></span> Synthesizing AI Investigation...`;
  }

  try {
    const inv = await API.startInvestigation(caseId);
    document.dispatchEvent(new CustomEvent('show-toast', {
      detail: {
        message: 'AI Investigation report generated successfully with evidence citations.',
        type: 'success'
      }
    }));
    renderInvestigationReport(inv, containerEl, caseId);
  } catch (err) {
    document.dispatchEvent(new CustomEvent('show-toast', {
      detail: { message: `AI Investigation failed: ${err.message}`, type: 'error' }
    }));
  } finally {
    if (triggerBtn) {
      triggerBtn.disabled = false;
      triggerBtn.innerHTML = `
        <svg class="btn-icon" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M10 2a1 1 0 011 1v1.323l3.954 1.582 1.599-.8a1 1 0 011.09.217l1.414 1.414a1 1 0 01.217 1.09l-.8 1.599L20 11.377V13a1 1 0 01-1 1h-1.323l-1.582 3.954.8 1.599a1 1 0 01-.217 1.09l-1.414 1.414a1 1 0 01-1.09.217l-1.599-.8L12.623 23H11a1 1 0 01-1-1v-1.323l-3.954-1.582-1.599.8a1 1 0 01-1.09-.217l-1.414-1.414a1 1 0 01-.217-1.09l.8-1.599L1 14.623V13a1 1 0 011-1h1.323l1.582-3.954-.8-1.599a1 1 0 01.217-1.09l1.414-1.414a1 1 0 011.09-.217l1.599.8L9.377 3H11a1 1 0 01-1-1z" clip-rule="evenodd"/>
        </svg>
        Re-Run AI Investigation
      `;
    }
  }
}

function renderEmptyInvestigationState(containerEl, caseId) {
  containerEl.innerHTML = `
    <div class="ai-investigation-panel">
      <div class="ai-header">
        <div class="ai-header-title">
          <span class="text-xs uppercase tracking-wider text-cyan font-mono">Autonomous Forensic Co-Pilot</span>
          <h3 class="panel-heading">AI Investigation & Evidence Synthesis</h3>
        </div>
      </div>
      <div class="empty-state empty-state-compact">
        <svg class="empty-icon-sm text-cyan" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z"/>
        </svg>
        <p class="empty-title">AI Investigation Not Yet Executed</p>
        <p class="empty-desc">Activate the AI Investigation Agent to synthesize evidence claims, explain discrepancies, and recommend investigative actions.</p>
        <button class="btn btn-primary btn-sm btn-trigger-ai" style="margin-top: 10px;">
          Execute AI Investigation
        </button>
      </div>
    </div>
  `;

  const btn = containerEl.querySelector('.btn-trigger-ai');
  if (btn) {
    btn.addEventListener('click', () => startInvestigationAction(caseId, containerEl, btn));
  }
}

function renderInvestigationReport(inv, containerEl, caseId) {
  const observations = inv.key_observations || [];
  const discrepancies = inv.identified_discrepancies || [];
  const recommendations = inv.recommended_actions || [];
  const missing = inv.missing_information || [];
  const supportingIds = inv.supporting_evidence_ids || [];

  containerEl.innerHTML = `
    <div class="ai-investigation-panel">
      <div class="ai-header">
        <div class="ai-header-title">
          <div class="text-xs uppercase tracking-wider text-cyan font-mono">FraudShield AI Forensic Co-Pilot &bull; Dossier Assessment</div>
          <div class="audit-title-row">
            <h3 class="panel-heading">AI Investigation Findings & Synthesis</h3>
            <span class="badge badge-resolved font-mono">${escapeHtml(inv.provider_used).toUpperCase()} &bull; ${escapeHtml(inv.model_used)}</span>
          </div>
        </div>
        <div class="audit-meta text-xs text-muted">
          Generated: ${formatDateTime(inv.created_at)}
        </div>
      </div>

      <!-- Impartiality Disclaimer -->
      <div class="audit-disclaimer" style="border-color: rgba(6, 182, 212, 0.3);">
        <svg class="disclaimer-icon" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
        </svg>
        <span>
          <strong>Investigative Safeguard:</strong> This AI assessment synthesizes documentary claims and Phase 4 deterministic findings.
          It does not determine legal guilt or intent. All findings require review by an authorized fraud analyst.
        </span>
      </div>

      <!-- Executive Synthesis -->
      <div class="audit-summary-box" style="border-left: 3px solid var(--accent-cyan);">
        <p class="summary-text">${escapeHtml(inv.summary)}</p>
      </div>

      <!-- Observations & Recommendations Grid -->
      <div class="audit-findings-grid">
        <!-- Column 1: Observations & Grounded Claims -->
        <div class="audit-column">
          <div class="finding-group-header text-cyan">
            <svg class="finding-icon" viewBox="0 0 20 20" fill="currentColor">
              <path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/>
              <path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"/>
            </svg>
            Key Observations (${observations.length})
          </div>

          <div class="finding-list">
            ${observations.length === 0 ? `
              <div class="empty-inline-finding text-muted">No specific observations recorded.</div>
            ` : observations.map(o => renderObservationCard(o)).join('')}
          </div>

          <!-- Identified Discrepancies Explained by AI -->
          ${discrepancies.length > 0 ? `
            <div class="finding-group-header text-danger" style="margin-top: 16px;">
              <svg class="finding-icon" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
              </svg>
              Discrepancies Analyzed (${discrepancies.length})
            </div>
            <div class="finding-list">
              ${discrepancies.map(d => renderDiscrepancyCard(d)).join('')}
            </div>
          ` : ''}
        </div>

        <!-- Column 2: Recommended Actions & Evidence Gaps -->
        <div class="audit-column">
          <div class="finding-group-header text-success">
            <svg class="finding-icon" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
            </svg>
            Recommended Next Actions (${recommendations.length})
          </div>

          <div class="finding-list">
            ${recommendations.length === 0 ? `
              <div class="empty-inline-finding text-muted">No specific actions recommended.</div>
            ` : recommendations.map(r => renderRecommendationCard(r)).join('')}
          </div>

          <!-- Missing Information / Evidence Gaps -->
          ${missing.length > 0 ? `
            <div class="finding-group-header text-warning" style="margin-top: 16px;">
              <svg class="finding-icon" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
              </svg>
              Evidence Gaps & Information Deficits (${missing.length})
            </div>
            <div class="finding-list">
              ${missing.map(m => `
                <div class="finding-card finding-warning">
                  <div class="finding-desc">${escapeHtml(m)}</div>
                </div>
              `).join('')}
            </div>
          ` : ''}

          <!-- Uncertainty Statement -->
          <div class="finding-card finding-info" style="margin-top: 16px;">
            <div class="finding-title text-cyan" style="font-size: 0.78rem;">Confidence & Limitation Statement</div>
            <p class="finding-desc">${escapeHtml(inv.confidence_explanation)}</p>
          </div>
        </div>
      </div>

      <!-- Follow-Up Q&A Chat Section -->
      <div class="ai-chat-section" id="ai-chat-container-${inv.id}">
        <div class="ai-chat-header">
          <div class="finding-title text-cyan">
            <svg class="finding-icon" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clip-rule="evenodd"/>
            </svg>
            Ask Follow-Up Question (Investigative Q&A)
          </div>
          <span class="text-xs text-muted">Answers grounded in case files and verification findings</span>
        </div>

        <div class="ai-chat-log" id="ai-chat-log-${inv.id}">
          <div class="skeleton-line" style="height: 24px; width: 60%;"></div>
        </div>

        <form class="ai-chat-input-form" id="ai-chat-form-${inv.id}">
          <input type="text" class="input input-sm ai-chat-input" id="ai-chat-input-${inv.id}" placeholder="Ask a question about this case (e.g. 'What is the tracking date anomaly?')..." required autocomplete="off" />
          <button type="submit" class="btn btn-primary btn-sm btn-send-chat" id="btn-send-chat-${inv.id}">
            Send
          </button>
        </form>
      </div>
    </div>
  `;

  // Initialize Chat Messages & Form
  setupChat(caseId, inv.id, containerEl);
}

function renderObservationCard(obs) {
  const evPills = (obs.evidence_ids || []).map(id => `
    <span class="evidence-ref-pill font-mono" title="Referenced Evidence ID">${id.substring(0, 8)}...</span>
  `).join('');

  const supportBadge = obs.is_supported === false 
    ? `<span class="badge badge-sm badge-rejected">UNSUPPORTED CLAIM</span>`
    : `<span class="badge badge-sm badge-resolved">CORROBORATED</span>`;

  return `
    <div class="finding-card ${obs.is_supported === false ? 'finding-critical' : 'finding-info'}">
      <div class="finding-header">
        <span class="finding-title">${escapeHtml(obs.title)}</span>
        ${supportBadge}
      </div>
      <p class="finding-desc">${escapeHtml(obs.observation)}</p>
      ${obs.support_note ? `<div class="text-xs text-muted" style="margin-top: 2px;">${escapeHtml(obs.support_note)}</div>` : ''}
      ${evPills ? `<div class="finding-evidence-row"><span class="text-muted text-xs">Evidence:</span> ${evPills}</div>` : ''}
    </div>
  `;
}

function renderDiscrepancyCard(disc) {
  const evPills = (disc.evidence_ids || []).map(id => `
    <span class="evidence-ref-pill font-mono" title="Referenced Evidence ID">${id.substring(0, 8)}...</span>
  `).join('');

  return `
    <div class="finding-card finding-${disc.severity === 'CRITICAL' ? 'critical' : 'warning'}">
      <div class="finding-header">
        <span class="finding-title">${escapeHtml(disc.title)}</span>
        <span class="badge badge-sm badge-${disc.severity === 'CRITICAL' ? 'rejected' : 'pending'}">${disc.severity}</span>
      </div>
      <p class="finding-desc">${escapeHtml(disc.explanation)}</p>
      ${evPills ? `<div class="finding-evidence-row"><span class="text-muted text-xs">Linked Evidence:</span> ${evPills}</div>` : ''}
    </div>
  `;
}

function renderRecommendationCard(rec) {
  const badgeClass = rec.priority === 'HIGH' ? 'badge-rejected' : (rec.priority === 'MEDIUM' ? 'badge-pending' : 'badge-outline');
  return `
    <div class="finding-card finding-match">
      <div class="finding-header">
        <span class="finding-title">${escapeHtml(rec.action)}</span>
        <span class="badge badge-sm ${badgeClass}">${rec.priority} PRIORITY</span>
      </div>
      <p class="finding-desc">${escapeHtml(rec.rationale)}</p>
    </div>
  `;
}

async function setupChat(caseId, investigationId, containerEl) {
  const chatLog = containerEl.querySelector(`#ai-chat-log-${investigationId}`);
  const form = containerEl.querySelector(`#ai-chat-form-${investigationId}`);
  const input = containerEl.querySelector(`#ai-chat-input-${investigationId}`);
  const sendBtn = containerEl.querySelector(`#btn-send-chat-${investigationId}`);

  async function refreshMessages() {
    try {
      const messages = await API.getInvestigationMessages(caseId, investigationId);
      if (messages.length === 0) {
        chatLog.innerHTML = `
          <div class="chat-placeholder text-muted text-xs">
            No follow-up messages yet. Ask a question to delve deeper into documentary evidence or discrepancies.
          </div>
        `;
        return;
      }

      chatLog.innerHTML = messages.map(m => {
        const isUser = m.sender === 'investigator';
        const evPills = (m.cited_evidence_ids || []).map(id => `
          <span class="evidence-ref-pill font-mono" title="Referenced Evidence ID">${id.substring(0, 8)}...</span>
        `).join('');

        return `
          <div class="chat-bubble ${isUser ? 'chat-bubble-user' : 'chat-bubble-assistant'}">
            <div class="chat-sender-label">${isUser ? 'Investigator' : 'AI Assistant'}</div>
            <div class="chat-message-text">${escapeHtml(m.message)}</div>
            ${evPills ? `<div class="finding-evidence-row" style="margin-top: 4px;"><span class="text-xs text-muted">Cited:</span> ${evPills}</div>` : ''}
          </div>
        `;
      }).join('');
      chatLog.scrollTop = chatLog.scrollHeight;
    } catch (e) {
      chatLog.innerHTML = `<div class="text-xs text-danger">Failed to load conversation history.</div>`;
    }
  }

  await refreshMessages();

  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const q = input.value.trim();
      if (!q) return;

      input.disabled = true;
      sendBtn.disabled = true;
      sendBtn.innerHTML = `<span class="spinner-sm"></span>`;

      try {
        await API.sendInvestigationChat(caseId, investigationId, q);
        input.value = '';
        await refreshMessages();
      } catch (err) {
        document.dispatchEvent(new CustomEvent('show-toast', {
          detail: { message: `Chat error: ${err.message}`, type: 'error' }
        }));
      } finally {
        input.disabled = false;
        sendBtn.disabled = false;
        sendBtn.innerHTML = 'Send';
        input.focus();
      }
    });
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

