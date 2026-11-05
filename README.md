# FraudShield
### AI-Powered Payment and Delivery Fraud Investigation Platform

FraudShield is an evidence-based fraud investigation platform designed to analyze payment disputes, delivery claims, and suspicious e-commerce transactions.

It combines document intelligence, deterministic verification, AI-powered investigation, and chronological event tracking to help investigators identify inconsistencies across payment receipts, order invoices, and delivery documents.

Instead of simply classifying transactions as fraudulent or legitimate, FraudShield analyzes available evidence, identifies discrepancies, explains its findings, and provides investigation recommendations with supporting evidence references.

**The system assists human investigators. It does not independently make final fraud decisions.**

---

## Problem Statement

Digital commerce has made online payments and deliveries easier, but it has also introduced challenges in resolving payment and delivery disputes.

Common scenarios include:

- Customers claiming that payment was completed but products were never delivered.
- Merchants reporting successful delivery while customers dispute receiving the product.
- Manipulated or inconsistent payment receipts.
- Differences between transaction amounts and order invoices.
- Duplicate transaction references.
- Conflicting delivery records.
- Insufficient evidence during refund investigations.

Manually investigating these disputes requires checking multiple documents and comparing transaction information.

FraudShield aims to simplify this process through automated evidence processing, verification, and AI-assisted investigation.

---

## Key Features

### 1. Case Management
- Create and manage investigation cases.
- Store customer, seller, order, and transaction information.
- Track case status.
- View and update case details.

### 2. Evidence Management
- Upload supporting documents.
- Store evidence files locally.
- Generate SHA-256 hashes for file integrity.
- Retrieve evidence metadata.
- Download and delete evidence.
- Maintain evidence associations with investigation cases.

### 3. OCR and Document Intelligence
- Extract text from PDF documents using PyMuPDF.
- Extract text from images using Tesseract OCR.
- Identify relevant payment information.
- Extract order and delivery details.
- Store extracted information against evidence records.
- Track OCR processing status and errors.

Information extraction includes:

| Payment Information | Order Information | Delivery Information |
|---|---|---|
| Transaction ID | Order ID | Tracking number |
| Payment amount | Order amount | Delivery date |
| Currency | Order date | Delivery status |
| Payment status | Product description | Recipient information |
| Payment date | Customer information | Delivery address |

### 4. Deterministic Fraud Verification Engine
- Compare payment and order amounts.
- Identify currency mismatches.
- Detect duplicate transaction references.
- Identify inconsistent dates.
- Compare order and delivery references.
- Detect recipient information mismatches.
- Identify missing evidence.
- Generate structured verification findings.

Verification results distinguish between matches, discrepancies, missing information, and unverified claims.

### 5. AI Investigation Agent
- Analyze case information and extracted document data.
- Interpret deterministic verification findings.
- Correlate related evidence.
- Generate investigation summaries.
- Explain identified discrepancies.
- Recommend additional investigation steps.
- Support follow-up questions about investigations.
- Reference supporting evidence IDs.

The AI agent uses existing verification findings and available evidence as its investigation context.

### 6. Automated Investigation Timeline
- Track case creation and updates.
- Record evidence upload and deletion events.
- Track OCR processing events.
- Record verification activities.
- Record AI investigation activities.
- Display events chronologically.
- Filter events by category.
- Support ascending and descending sorting.
- Preserve historical timeline events.

---

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python |
| API Framework | FastAPI |
| Database | SQLite |
| ORM | SQLAlchemy |
| Data Validation | Pydantic |
| PDF Text Extraction | PyMuPDF |
| Image OCR | Tesseract OCR, pytesseract |
| HTTP Client | HTTPX |
| AI Integration | Configurable LLM API |
| File Integrity | SHA-256 |
| API Documentation | Swagger UI |

### Architecture

```text
                  FraudShield
                       |
          +------------+------------+
          |                         |
       Frontend                  Backend
    HTML/CSS/JS                 FastAPI
          |                         |
          |              +----------+----------+
          |              |          |          |
          |           Case      Evidence     OCR
          |         Management  Management Processing
          |              |          |          |
          |              +----------+----------+
          |                         |
          |                Verification Engine
          |                         |
          |                 AI Investigation
          |                       Agent
          |                         |
          |               Investigation Timeline
          |                         |
          +-------------------------+
                                    |
                           SQLite Database
                                    |
                            Evidence Storage
```

---

## Project Structure

```text
FraudShield/
│
├── backend/
│   ├── app/
│   │   ├── models/
│   │   ├── routes/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── database.py
│   │   ├── main.py
│   │   └── storage.py
│   │
│   ├── storage/
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── index.html
│   ├── css/
│   │   └── style.css
│   │
│   └── js/
│       ├── api.js
│       ├── app.js
│       ├── cases.js
│       ├── investigations.js
│       └── timeline.js
│
├── .gitignore
└── README.md
```

*The exact files and folders may vary as the project develops.*

---

## Installation and Setup

### Prerequisites

Install the following:

- Python 3.10 or later.
- Git.
- Tesseract OCR.
- A modern web browser.
- An LLM API key if using an external AI provider.

### 1. Clone the Repository

```bash
git clone https://github.com/Tarunika-Muruganathan/FraudShield.git
```

Navigate into the project:

```bash
cd FraudShield
```

### 2. Create a Virtual Environment

Navigate to the backend:

```bash
cd backend
```

Create the virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Tesseract OCR

Install Tesseract OCR on your operating system.

On Windows, make sure the Tesseract installation directory is included in your system PATH.

Verify the installation:

```powershell
tesseract --version
```

### 5. Configure Environment Variables

If your project uses an external LLM provider, configure its credentials in a local `.env` file.

Example configuration:

```env
LLM_PROVIDER=mock
LLM_API_KEY=
LLM_BASE_URL=
LLM_MODEL=
LLM_TIMEOUT=30
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=2048
```

The mock provider can be used for local testing without an external API key, provided it is supported by the current implementation.

For an external provider, configure the appropriate provider, API key, base URL, and model.

**Never commit API keys or secret credentials to GitHub.**

---

## Running FraudShield

### 1. Start the Backend

Make sure you are inside the `backend` directory and your virtual environment is activated.

Run:

```powershell
uvicorn app.main:app --reload
```

The backend should start at:

```text
http://127.0.0.1:8000
```

### 2. Open the Frontend

If the frontend is mounted through FastAPI, open:

```text
http://127.0.0.1:8000/app/
```

If the frontend is not mounted through FastAPI, use VS Code Live Server:

1. Open the FraudShield project in VS Code.
2. Navigate to `frontend/index.html`.
3. Right-click the file.
4. Select **Open with Live Server**.

The frontend will typically be available at:

```text
http://127.0.0.1:5500
```

When using Live Server, ensure the frontend API configuration points to the running FastAPI backend and that CORS permits the frontend origin.

### 3. Access API Documentation

FastAPI Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

Backend health check:

```text
http://127.0.0.1:8000/health
```

---

## Application Workflow

The typical FraudShield investigation workflow is:

```text
Create Investigation Case
           |
           v
Upload Supporting Evidence
           |
           v
Extract Document Information
           |
           v
Run OCR Processing
           |
           v
Run Deterministic Verification
           |
           v
Generate AI Investigation
           |
           v
Review Investigation Findings
           |
           v
View Investigation Timeline
           |
           v
Human Review and Decision
```

### Example Investigation

Consider an online purchase where a customer claims that payment was completed but the product was not received.

FraudShield can:

1. Register the dispute as an investigation case.
2. Collect the payment receipt, order invoice, and delivery proof.
3. Extract transaction and delivery information.
4. Compare payment and order amounts.
5. Identify inconsistencies between order and delivery information.
6. Generate an AI-assisted investigation summary.
7. Record investigation activities in the timeline.
8. Present findings and supporting evidence for human review.

---

## Security and Data Integrity

FraudShield incorporates several security and integrity considerations:

- SHA-256 hashing for uploaded evidence.
- Original evidence files are preserved during OCR processing.
- API credentials are stored in environment variables.
- Uploaded document contents are treated as untrusted input.
- AI-generated evidence references are validated.
- Investigation data is associated with its corresponding case.
- Historical investigation activities are preserved.
- AI-generated findings do not automatically determine fraud.

**Important:** OCR-extracted information represents claims contained in documents. It does not independently prove that a payment or delivery occurred.

---

## Testing

Run the automated tests from the backend directory:

```powershell
python -m pytest -q
```

The test suite should cover the functionality implemented across the development phases.

Important test areas include:

- Case creation, retrieval, updates, and deletion.
- Evidence upload and deletion.
- File integrity verification.
- OCR extraction and error handling.
- Duplicate OCR processing prevention.
- Payment and order verification.
- Delivery discrepancy detection.
- AI response validation.
- Evidence citation validation.
- Prompt injection handling.
- Investigation history.
- Timeline ordering and filtering.
- Regression testing across previous modules.

Use synthetic documents and test data when testing the application.

---

## Development Roadmap

| Phase | Description |
|---|---|
| Phase 1 | Backend Foundation and Case Management |
| Phase 2 | Evidence Management |
| Phase 3 | OCR and Document Intelligence |
| Phase 4 | Deterministic Fraud Verification Engine |
| Phase 5 | AI Investigation Agent |
| Phase 6 | Automated Investigation Timeline |
| Phase 7 | Evidence-Backed Investigation Reports |
| Phase 8 | Final Testing, Security and Deployment |

---

## Current Limitations

- OCR accuracy depends on document quality and readability.
- Extracted information may require manual correction or review.
- An uploaded receipt does not independently establish payment completion.
- A delivery document does not independently establish that the customer received the product.
- External LLM functionality depends on provider availability and configuration.
- Human review is required before making final investigation decisions.
- Production deployment requires additional security, authentication, access-control, and operational hardening.

---

## Future Improvements

Potential future enhancements include:

- Automated PDF investigation report generation.
- Integration with verified payment provider APIs.
- Courier tracking API integration.
- Role-based investigator access.
- Secure cloud-based evidence storage.
- Advanced audit and reporting capabilities.
- Production deployment and monitoring.

---

## Repository

**GitHub:** https://github.com/Tarunika-Muruganathan/FraudShield

---

## Disclaimer

FraudShield is an investigation assistance project developed for educational and practical software engineering purposes.

It is designed to help analyze evidence and identify inconsistencies in payment and delivery disputes.

Its outputs are investigative indicators and recommendations, not definitive legal conclusions or independent proof of fraud.

All final decisions should be made by authorized human investigators after reviewing the available evidence.

---

**FraudShield — Investigate with Evidence. Verify with Logic. Decide with Confidence.**