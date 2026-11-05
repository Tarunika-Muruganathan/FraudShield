/**
 * FraudShield - API Client
 * Communicates with the FastAPI backend at http://127.0.0.1:8000
 */

const API_BASE_URL = window.location.origin.includes(':8000') 
  ? window.location.origin 
  : 'http://127.0.0.1:8000';

class ApiError extends Error {
  constructor(message, status, details = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

/**
 * Generic request helper with error handling
 */
async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  const defaultHeaders = {};

  if (!(options.body instanceof FormData)) {
    defaultHeaders['Content-Type'] = 'application/json';
  }

  const config = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...(options.headers || {})
    }
  };

  try {
    const response = await fetch(url, config);

    // 204 No Content
    if (response.status === 204) {
      return null;
    }

    let data = null;
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      data = await response.json();
    } else {
      data = await response.text();
    }

    if (!response.ok) {
      let errorMessage = `Request failed with status ${response.status}`;
      if (data && typeof data === 'object') {
        if (typeof data.detail === 'string') {
          errorMessage = data.detail;
        } else if (Array.isArray(data.detail)) {
          errorMessage = data.detail.map(d => `${d.loc ? d.loc.join('.') + ': ' : ''}${d.msg}`).join(', ');
        }
      } else if (typeof data === 'string' && data.length > 0) {
        errorMessage = data;
      }
      throw new ApiError(errorMessage, response.status, data);
    }

    return data;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    // Network errors, connection refused, CORS failure
    throw new ApiError(
      `Cannot connect to API server at ${API_BASE_URL}. Ensure the backend is running.`,
      0,
      error
    );
  }
}

export const API = {
  baseUrl: API_BASE_URL,

  // Health
  async checkHealth() {
    return apiRequest('/health', { method: 'GET' });
  },

  // Cases
  async getCases() {
    return apiRequest('/api/cases/', { method: 'GET' });
  },

  async getCase(caseId) {
    return apiRequest(`/api/cases/${encodeURIComponent(caseId)}`, { method: 'GET' });
  },

  async createCase(caseData) {
    return apiRequest('/api/cases/', {
      method: 'POST',
      body: JSON.stringify(caseData)
    });
  },

  async updateCase(caseId, updateData) {
    return apiRequest(`/api/cases/${encodeURIComponent(caseId)}`, {
      method: 'PATCH',
      body: JSON.stringify(updateData)
    });
  },

  async deleteCase(caseId) {
    return apiRequest(`/api/cases/${encodeURIComponent(caseId)}`, {
      method: 'DELETE'
    });
  },

  // Evidence
  async getCaseEvidence(caseId) {
    return apiRequest(`/api/cases/${encodeURIComponent(caseId)}/evidence/`, {
      method: 'GET'
    });
  },

  async uploadEvidence(caseId, file, onProgress = null) {
    const url = `${API_BASE_URL}/api/cases/${encodeURIComponent(caseId)}/evidence/`;
    const formData = new FormData();
    formData.append('file', file);

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open('POST', url, true);

      if (xhr.upload && onProgress) {
        xhr.upload.onprogress = (event) => {
          if (event.lengthComputable) {
            const percentComplete = Math.round((event.loaded / event.total) * 100);
            onProgress(percentComplete);
          }
        };
      }

      xhr.onload = () => {
        let responseData = null;
        try {
          responseData = JSON.parse(xhr.responseText);
        } catch (e) {
          responseData = xhr.responseText;
        }

        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(responseData);
        } else {
          let msg = `Upload failed with status ${xhr.status}`;
          if (responseData && typeof responseData === 'object' && responseData.detail) {
            msg = typeof responseData.detail === 'string' 
              ? responseData.detail 
              : JSON.stringify(responseData.detail);
          }
          reject(new ApiError(msg, xhr.status, responseData));
        }
      };

      xhr.onerror = () => {
        reject(new ApiError('Network error occurred during evidence file upload.', 0));
      };

      xhr.send(formData);
    });
  },

  async getEvidenceMetadata(evidenceId) {
    return apiRequest(`/api/evidence/${encodeURIComponent(evidenceId)}`, {
      method: 'GET'
    });
  },

  async downloadEvidence(evidenceId, defaultFilename = 'evidence_file') {
    const url = `${API_BASE_URL}/api/evidence/${encodeURIComponent(evidenceId)}/download`;
    const response = await fetch(url, { method: 'GET' });
    
    if (!response.ok) {
      let msg = `Download failed with status ${response.status}`;
      try {
        const errorJson = await response.json();
        if (errorJson.detail) msg = errorJson.detail;
      } catch (e) {}
      throw new ApiError(msg, response.status);
    }

    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = downloadUrl;
    a.download = defaultFilename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(downloadUrl);
  },

  async deleteEvidence(evidenceId) {
    return apiRequest(`/api/evidence/${encodeURIComponent(evidenceId)}`, {
      method: 'DELETE'
    });
  },

  // Document Intelligence & OCR
  async processOcr(evidenceId, force = false) {
    return apiRequest(`/api/evidence/${encodeURIComponent(evidenceId)}/process-ocr?force=${Boolean(force)}`, {
      method: 'POST'
    });
  },

  async getEvidenceOcr(evidenceId) {
    return apiRequest(`/api/evidence/${encodeURIComponent(evidenceId)}/ocr`, {
      method: 'GET'
    });
  },

  async getEvidenceExtractedData(evidenceId) {
    return apiRequest(`/api/evidence/${encodeURIComponent(evidenceId)}/extracted-data`, {
      method: 'GET'
    });
  },

  // Fraud Verification Engine
  async verifyCase(caseId) {
    return apiRequest(`/api/cases/${encodeURIComponent(caseId)}/verify`, {
      method: 'POST'
    });
  },

  async getCaseVerification(caseId) {
    return apiRequest(`/api/cases/${encodeURIComponent(caseId)}/verification`, {
      method: 'GET'
    });
  },

  async getCaseVerificationHistory(caseId) {
    return apiRequest(`/api/cases/${encodeURIComponent(caseId)}/verifications`, {
      method: 'GET'
    });
  },

  // AI Investigation Agent
  async startInvestigation(caseId) {
    return apiRequest(`/api/cases/${encodeURIComponent(caseId)}/investigations`, {
      method: 'POST'
    });
  },

  async getLatestInvestigation(caseId) {
    return apiRequest(`/api/cases/${encodeURIComponent(caseId)}/investigations/latest`, {
      method: 'GET'
    });
  },

  async getInvestigationHistory(caseId) {
    return apiRequest(`/api/cases/${encodeURIComponent(caseId)}/investigations`, {
      method: 'GET'
    });
  },

  async sendInvestigationChat(caseId, investigationId, message) {
    return apiRequest(`/api/cases/${encodeURIComponent(caseId)}/investigations/${encodeURIComponent(investigationId)}/chat`, {
      method: 'POST',
      body: JSON.stringify({ message })
    });
  },

  async getInvestigationMessages(caseId, investigationId) {
    return apiRequest(`/api/cases/${encodeURIComponent(caseId)}/investigations/${encodeURIComponent(investigationId)}/messages`, {
      method: 'GET'
    });
  }
};

