/**
 * FraudShield - Evidence Management & Document Intelligence Module
 * Handles file uploads, drag-and-drop, SHA-256 displays, Tesseract OCR, and structured field extraction.
 */

import { API } from './api.js';

let currentCaseId = null;
let evidenceListCache = [];

export async function loadCaseEvidence(caseId, containerEl, onEvidenceChanged) {
  currentCaseId = caseId;
  containerEl.innerHTML = `
    <div class="evidence-section-header">
      <div class="section-title-wrap">
        <svg class="section-icon text-cyan" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
          <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"/>
        </svg>
        <h3 class="section-title">Evidence Locker & Intel</h3>
        <span class="badge badge-outline" id="evidence-count-badge">Loading...</span>
      </div>
    </div>

    <!-- Upload Drop Zone -->
    <div class="upload-dropzone" id="evidence-dropzone">
      <input type="file" id="evidence-file-input" class="file-input-hidden" accept=".pdf,.png,.jpg,.jpeg,image/png,image/jpeg,application/pdf" />
      <div class="dropzone-content">
        <div class="dropzone-icon-wrap">
          <svg class="dropzone-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 16.5V9.75m0 0l3 3m-3-3l-3 3M6.75 19.5a4.5 4.5 0 01-1.41-8.775 5.25 5.25 0 0110.233-2.33 3 3 0 013.758 3.848A3.752 3.752 0 0118 19.5H6.75z"/>
          </svg>
        </div>
        <div class="dropzone-text">
          <p class="dropzone-prompt"><strong>Click to upload</strong> or drag and drop evidence</p>
          <p class="dropzone-hint">PDF, PNG, JPG, or JPEG (Max 10 MB per file)</p>
        </div>
      </div>
      <!-- Progress Bar -->
      <div class="upload-progress-container hidden" id="upload-progress-wrap">
        <div class="upload-progress-header">
          <span class="text-sm text-cyan font-mono" id="upload-progress-status">Uploading: 0%</span>
          <span class="text-sm text-muted" id="upload-filename">filename.pdf</span>
        </div>
        <div class="progress-track">
          <div class="progress-fill progress-fill-cyan" id="upload-progress-bar" style="width: 0%"></div>
        </div>
      </div>
      <!-- Upload Error Banner -->
      <div class="alert alert-danger hidden" id="upload-error-alert"></div>
    </div>

    <!-- Evidence Items Container -->
    <div class="evidence-list" id="evidence-items-container">
      <div class="skeleton-list">
        <div class="skeleton-line" style="height: 80px; margin-bottom: 12px;"></div>
        <div class="skeleton-line" style="height: 80px;"></div>
      </div>
    </div>
  `;

  setupDropzone(caseId, containerEl, onEvidenceChanged);
  await refreshEvidenceList(caseId, containerEl, onEvidenceChanged);
}

function setupDropzone(caseId, containerEl, onEvidenceChanged) {
  const dropzone = containerEl.querySelector('#evidence-dropzone');
  const fileInput = containerEl.querySelector('#evidence-file-input');
  const progressWrap = containerEl.querySelector('#upload-progress-wrap');

  dropzone.addEventListener('click', (e) => {
    if (e.target.closest('.alert') || !progressWrap.classList.contains('hidden')) return;
    fileInput.click();
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files && fileInput.files[0]) {
      handleFileUpload(fileInput.files[0], caseId, containerEl, onEvidenceChanged);
      fileInput.value = '';
    }
  });

  ['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add('dropzone-active');
    });
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove('dropzone-active');
    });
  });

  dropzone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    if (dt && dt.files && dt.files.length > 0) {
      handleFileUpload(dt.files[0], caseId, containerEl, onEvidenceChanged);
    }
  });
}

async function handleFileUpload(file, caseId, containerEl, onEvidenceChanged) {
  const errorAlert = containerEl.querySelector('#upload-error-alert');
  const progressWrap = containerEl.querySelector('#upload-progress-wrap');
  const progressBar = containerEl.querySelector('#upload-progress-bar');
  const progressStatus = containerEl.querySelector('#upload-progress-status');
  const uploadFilename = containerEl.querySelector('#upload-filename');
  const dropzoneContent = containerEl.querySelector('.dropzone-content');

  errorAlert.classList.add('hidden');
  errorAlert.textContent = '';

  const allowedExtensions = ['.pdf', '.png', '.jpg', '.jpeg'];
  const ext = '.' + file.name.split('.').pop().toLowerCase();
  
  if (!allowedExtensions.includes(ext)) {
    errorAlert.textContent = `File extension '${ext}' is not supported. Please upload a PDF, PNG, JPG, or JPEG file.`;
    errorAlert.classList.remove('hidden');
    return;
  }

  const maxSize = 10 * 1024 * 1024;
  if (file.size > maxSize) {
    errorAlert.textContent = `File size (${formatFileSize(file.size)}) exceeds the maximum allowed limit of 10 MB.`;
    errorAlert.classList.remove('hidden');
    return;
  }

  if (file.size === 0) {
    errorAlert.textContent = 'Selected file is empty (0 bytes). Please select a valid document or image.';
    errorAlert.classList.remove('hidden');
    return;
  }

  dropzoneContent.classList.add('opacity-40');
  progressWrap.classList.remove('hidden');
  uploadFilename.textContent = file.name;
  progressBar.style.width = '0%';
  progressStatus.textContent = 'Uploading: 0%';

  try {
    await API.uploadEvidence(caseId, file, (percent) => {
      progressBar.style.width = `${percent}%`;
      progressStatus.textContent = `Uploading: ${percent}%`;
    });

    progressBar.style.width = '100%';
    progressStatus.textContent = 'Verifying SHA-256 & Saving...';

    await refreshEvidenceList(caseId, containerEl, onEvidenceChanged);
    document.dispatchEvent(new CustomEvent('show-toast', {
      detail: { message: `Evidence '${file.name}' securely uploaded & indexed.`, type: 'success' }
    }));
  } catch (err) {
    errorAlert.textContent = err.message || 'Evidence upload failed.';
    errorAlert.classList.remove('hidden');
  } finally {
    progressWrap.classList.add('hidden');
    dropzoneContent.classList.remove('opacity-40');
  }
}

async function refreshEvidenceList(caseId, containerEl, onEvidenceChanged) {
  const itemsContainer = containerEl.querySelector('#evidence-items-container');
  const countBadge = containerEl.querySelector('#evidence-count-badge');

  try {
    const evidenceList = await API.getCaseEvidence(caseId);
    evidenceListCache = evidenceList;

    if (countBadge) {
      countBadge.textContent = `${evidenceList.length} ${evidenceList.length === 1 ? 'file' : 'files'}`;
    }

    if (!evidenceList || evidenceList.length === 0) {
      itemsContainer.innerHTML = `
        <div class="empty-state empty-state-compact">
          <svg class="empty-icon-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"/>
          </svg>
          <p class="empty-title">No Evidence Uploaded Yet</p>
          <p class="empty-desc">Attach payment slips, delivery photos, or courier tracking confirmations above.</p>
        </div>
      `;
      return;
    }

    itemsContainer.innerHTML = `
      <div class="evidence-grid">
        ${evidenceList.map(item => renderEvidenceCard(item)).join('')}
      </div>
    `;

    // Download handlers
    itemsContainer.querySelectorAll('.btn-download-evidence').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        e.stopPropagation();
        const evId = btn.getAttribute('data-evidence-id');
        const filename = btn.getAttribute('data-filename');
        btn.disabled = true;
        try {
          await API.downloadEvidence(evId, filename);
        } catch (err) {
          document.dispatchEvent(new CustomEvent('show-toast', {
            detail: { message: `Download error: ${err.message}`, type: 'error' }
          }));
        } finally {
          btn.disabled = false;
        }
      });
    });

    // Delete handlers
    itemsContainer.querySelectorAll('.btn-delete-evidence').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const evId = btn.getAttribute('data-evidence-id');
        const filename = btn.getAttribute('data-filename');

        document.dispatchEvent(new CustomEvent('open-confirm-modal', {
          detail: {
            title: 'Delete Evidence File',
            message: `Permanently delete evidence file '${filename}'? This cannot be undone and will unlink the file from disk.`,
            confirmText: 'Delete Evidence',
            isDestructive: true,
            onConfirm: async () => {
              try {
                await API.deleteEvidence(evId);
                document.dispatchEvent(new CustomEvent('show-toast', {
                  detail: { message: `Evidence '${filename}' deleted.`, type: 'info' }
                }));
                await refreshEvidenceList(caseId, containerEl, onEvidenceChanged);
                if (onEvidenceChanged) onEvidenceChanged();
              } catch (err) {
                document.dispatchEvent(new CustomEvent('show-toast', {
                  detail: { message: `Deletion error: ${err.message}`, type: 'error' }
                }));
              }
            }
          }
        }));
      });
    });

    // Copy SHA-256 hash
    itemsContainer.querySelectorAll('.btn-copy-hash').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const hash = btn.getAttribute('data-hash');
        navigator.clipboard.writeText(hash).then(() => {
          document.dispatchEvent(new CustomEvent('show-toast', {
            detail: { message: 'SHA-256 hash copied to clipboard', type: 'info' }
          }));
        });
      });
    });

    // Run / Re-run OCR handlers
    itemsContainer.querySelectorAll('.btn-trigger-ocr').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        e.stopPropagation();
        const evId = btn.getAttribute('data-evidence-id');
        const isForce = btn.getAttribute('data-force') === 'true';

        btn.disabled = true;
        btn.innerHTML = `<span class="spinner-sm"></span> OCR Processing...`;

        try {
          const docData = await API.processOcr(evId, isForce);
          document.dispatchEvent(new CustomEvent('show-toast', {
            detail: {
              message: docData.ocr_status === 'completed' 
                ? 'Document OCR & intelligence extraction completed.' 
                : `OCR finished with status: ${docData.ocr_status}`,
              type: docData.ocr_status === 'completed' ? 'success' : 'warning'
            }
          }));
          await refreshEvidenceList(caseId, containerEl, onEvidenceChanged);
          if (onEvidenceChanged) onEvidenceChanged();
        } catch (err) {
          document.dispatchEvent(new CustomEvent('show-toast', {
            detail: { message: `OCR error: ${err.message}`, type: 'error' }
          }));
          btn.disabled = false;
          btn.innerHTML = `Run OCR`;
        }
      });
    });

    // Toggle Intel Drawer
    itemsContainer.querySelectorAll('.btn-toggle-intel').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const evId = btn.getAttribute('data-evidence-id');
        const drawer = itemsContainer.querySelector(`#intel-drawer-${evId}`);
        if (drawer) {
          drawer.classList.toggle('hidden');
          const isExpanded = !drawer.classList.contains('hidden');
          btn.innerHTML = isExpanded 
            ? `Hide Intel &and;` 
            : `View Extracted Intel &or;`;
        }
      });
    });

    // Copy raw OCR text
    itemsContainer.querySelectorAll('.btn-copy-ocr-text').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const evId = btn.getAttribute('data-evidence-id');
        const textPre = itemsContainer.querySelector(`#ocr-raw-text-${evId}`);
        if (textPre) {
          navigator.clipboard.writeText(textPre.textContent).then(() => {
            document.dispatchEvent(new CustomEvent('show-toast', {
              detail: { message: 'Raw OCR text copied to clipboard', type: 'info' }
            }));
          });
        }
      });
    });

  } catch (err) {
    itemsContainer.innerHTML = `
      <div class="alert alert-danger">
        Failed to load case evidence: ${escapeHtml(err.message)}
      </div>
    `;
  }
}

function renderEvidenceCard(item) {
  const isPdf = item.filename.toLowerCase().endsWith('.pdf') || (item.content_type && item.content_type.includes('pdf'));
  const shortHash = item.sha256_hash ? `${item.sha256_hash.substring(0, 10)}...${item.sha256_hash.substring(item.sha256_hash.length - 8)}` : '—';
  const doc = item.document_data;
  const ocrStatus = doc ? doc.ocr_status : (item.extracted_text ? 'completed' : 'pending');

  let ocrBadgeHtml = '';
  let ocrActionBtnHtml = '';

  if (ocrStatus === 'completed') {
    ocrBadgeHtml = `<span class="badge badge-resolved">OCR Analyzed</span>`;
    ocrActionBtnHtml = `
      <button class="btn btn-ghost btn-xs btn-toggle-intel" data-evidence-id="${item.evidence_id}">
        View Extracted Intel &or;
      </button>
      <button class="btn btn-ghost btn-xs btn-trigger-ocr" data-evidence-id="${item.evidence_id}" data-force="true" title="Re-run Tesseract OCR">
        Re-Scan
      </button>
    `;
  } else if (ocrStatus === 'unreadable') {
    ocrBadgeHtml = `<span class="badge badge-pending">Unreadable Document</span>`;
    ocrActionBtnHtml = `
      <button class="btn btn-ghost-danger btn-xs btn-toggle-intel" data-evidence-id="${item.evidence_id}">
        View Diagnosis &or;
      </button>
      <button class="btn btn-ghost btn-xs btn-trigger-ocr" data-evidence-id="${item.evidence_id}" data-force="true">
        Retry OCR
      </button>
    `;
  } else if (ocrStatus === 'failed') {
    ocrBadgeHtml = `<span class="badge badge-rejected">OCR Failed</span>`;
    ocrActionBtnHtml = `
      <button class="btn btn-ghost-danger btn-xs btn-toggle-intel" data-evidence-id="${item.evidence_id}">
        View Error &or;
      </button>
      <button class="btn btn-ghost btn-xs btn-trigger-ocr" data-evidence-id="${item.evidence_id}" data-force="true">
        Retry OCR
      </button>
    `;
  } else {
    ocrBadgeHtml = `<span class="badge badge-outline">OCR Pending</span>`;
    ocrActionBtnHtml = `
      <button class="btn btn-primary btn-xs btn-trigger-ocr" data-evidence-id="${item.evidence_id}" data-force="false">
        <svg class="action-icon" viewBox="0 0 20 20" fill="currentColor">
          <path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/>
          <path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"/>
        </svg>
        Extract Intel
      </button>
    `;
  }

  return `
    <div class="evidence-card" data-evidence-id="${item.evidence_id}">
      <div class="evidence-card-header">
        <div class="evidence-badge-group">
          <span class="evidence-type-badge ${isPdf ? 'badge-pdf' : 'badge-img'}">
            ${isPdf ? 'PDF' : 'IMAGE'}
          </span>
          ${ocrBadgeHtml}
        </div>
        <div class="evidence-actions">
          ${ocrActionBtnHtml}
          <button class="btn btn-ghost btn-xs btn-download-evidence" data-evidence-id="${item.evidence_id}" data-filename="${escapeHtml(item.filename)}" title="Download file">
            <svg class="action-icon" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd"/>
            </svg>
            Download
          </button>
          <button class="btn btn-ghost-danger btn-xs btn-delete-evidence" data-evidence-id="${item.evidence_id}" data-filename="${escapeHtml(item.filename)}" title="Delete file">
            <svg class="action-icon text-danger" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd"/>
            </svg>
          </button>
        </div>
      </div>

      <div class="evidence-filename" title="${escapeHtml(item.filename)}">
        ${escapeHtml(item.filename)}
      </div>

      <div class="evidence-meta-row">
        <span class="evidence-meta-label">Size:</span>
        <span class="evidence-meta-value font-mono">${formatFileSize(item.file_size)}</span>
        <span class="meta-dot">&bull;</span>
        <span class="evidence-meta-label">Uploaded:</span>
        <span class="evidence-meta-value">${formatDate(item.uploaded_at)}</span>
      </div>

      <div class="evidence-hash-box">
        <div class="hash-label-wrap">
          <span class="hash-tag">SHA-256</span>
          <button class="btn-copy-hash" data-hash="${escapeHtml(item.sha256_hash)}" title="Copy full cryptographic hash">
            <svg class="copy-icon" viewBox="0 0 20 20" fill="currentColor">
              <path d="M8 3a1 1 0 011-1h2a1 1 0 110 2H9a1 1 0 01-1-1z"/>
              <path d="M6 3a2 2 0 00-2 2v11a2 2 0 002 2h8a2 2 0 002-2V5a2 2 0 00-2-2 3 3 0 01-3 3H9a3 3 0 01-3-3z"/>
            </svg>
            Copy
          </button>
        </div>
        <div class="hash-code font-mono" title="${escapeHtml(item.sha256_hash)}">${shortHash}</div>
      </div>

      <!-- Collapsible Intel Drawer -->
      <div class="ocr-intel-drawer hidden" id="intel-drawer-${item.evidence_id}">
        ${renderIntelContent(doc, item.extracted_text, item.evidence_id)}
      </div>
    </div>
  `;
}

function renderIntelContent(doc, fallbackText, evidenceId) {
  if (!doc && !fallbackText) {
    return `<div class="empty-inline-state">No OCR intelligence available. Click 'Extract Intel' above.</div>`;
  }

  const rawText = (doc && doc.raw_text) ? doc.raw_text : fallbackText;
  const ocrStatus = doc ? doc.ocr_status : 'completed';

  let errorAlert = '';
  if (doc && doc.ocr_error) {
    errorAlert = `
      <div class="alert alert-danger" style="margin-bottom: 12px;">
        <strong>OCR Diagnosis:</strong> ${escapeHtml(doc.ocr_error)}
      </div>
    `;
  }

  // Structured Information Grid
  const amountStr = doc && doc.payment_amount 
    ? `${escapeHtml(doc.currency || '')} ${escapeHtml(doc.payment_amount)}`.trim()
    : null;

  return `
    ${errorAlert}
    <div class="intel-section-title">
      <svg class="intel-icon text-cyan" viewBox="0 0 20 20" fill="currentColor">
        <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z"/>
        <path fill-rule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z" clip-rule="evenodd"/>
      </svg>
      Extracted Document Intelligence
    </div>

    <div class="ocr-fields-grid">
      <div class="ocr-field-item">
        <span class="ocr-field-label">Transaction ID</span>
        <span class="ocr-field-val font-mono">${doc && doc.transaction_id ? escapeHtml(doc.transaction_id) : '<span class="text-muted">—</span>'}</span>
      </div>
      <div class="ocr-field-item">
        <span class="ocr-field-label">Order ID</span>
        <span class="ocr-field-val font-mono text-cyan">${doc && doc.order_id ? escapeHtml(doc.order_id) : '<span class="text-muted">—</span>'}</span>
      </div>
      <div class="ocr-field-item">
        <span class="ocr-field-label">Amount & Currency</span>
        <span class="ocr-field-val font-mono">${amountStr ? amountStr : '<span class="text-muted">—</span>'}</span>
      </div>
      <div class="ocr-field-item">
        <span class="ocr-field-label">Payment Status</span>
        <span class="ocr-field-val">${doc && doc.payment_status ? `<span class="badge badge-resolved">${escapeHtml(doc.payment_status)}</span>` : '<span class="text-muted">—</span>'}</span>
      </div>
      <div class="ocr-field-item">
        <span class="ocr-field-label">Payment Date</span>
        <span class="ocr-field-val">${doc && doc.payment_date ? escapeHtml(doc.payment_date) : '<span class="text-muted">—</span>'}</span>
      </div>
      <div class="ocr-field-item">
        <span class="ocr-field-label">Sender / Payer</span>
        <span class="ocr-field-val">${doc && doc.sender_name ? escapeHtml(doc.sender_name) : '<span class="text-muted">—</span>'}</span>
      </div>
      <div class="ocr-field-item">
        <span class="ocr-field-label">Receiver / Payee</span>
        <span class="ocr-field-val">${doc && doc.receiver_name ? escapeHtml(doc.receiver_name) : '<span class="text-muted">—</span>'}</span>
      </div>
      <div class="ocr-field-item">
        <span class="ocr-field-label">Tracking Number</span>
        <span class="ocr-field-val font-mono">${doc && doc.tracking_number ? escapeHtml(doc.tracking_number) : '<span class="text-muted">—</span>'}</span>
      </div>
      <div class="ocr-field-item">
        <span class="ocr-field-label">Delivery Date</span>
        <span class="ocr-field-val">${doc && doc.delivery_date ? escapeHtml(doc.delivery_date) : '<span class="text-muted">—</span>'}</span>
      </div>
      <div class="ocr-field-item">
        <span class="ocr-field-label">Delivery Status</span>
        <span class="ocr-field-val">${doc && doc.delivery_status ? `<span class="badge badge-investigating">${escapeHtml(doc.delivery_status)}</span>` : '<span class="text-muted">—</span>'}</span>
      </div>
    </div>

    <!-- Raw OCR Text -->
    <div class="ocr-raw-section">
      <div class="ocr-raw-header">
        <span class="ocr-field-label">Raw Tesseract OCR Text</span>
        <button class="btn btn-ghost btn-xs btn-copy-ocr-text" data-evidence-id="${evidenceId}">
          Copy Raw Text
        </button>
      </div>
      <pre class="ocr-text-pre font-mono" id="ocr-raw-text-${evidenceId}">${rawText ? escapeHtml(rawText) : '<span class="text-muted">No text was recognized in this document.</span>'}</pre>
    </div>
  `;
}

function formatFileSize(bytes) {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
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
