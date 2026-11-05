# Payment-to-Delivery Fraud Investigation Agent

Phase 1 starter project: FastAPI case-management API with SQLite.

## Requirements
- Python 3.10+
- PowerShell or a compatible terminal

## Setup (Windows PowerShell)

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

If PowerShell blocks activation:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Open http://127.0.0.1:8000/docs for Swagger UI.

The SQLite database is created automatically at `backend/fraud_investigator.db`.

## Implemented endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/cases/` | Create a case |
| GET | `/api/cases/` | List cases |
| GET | `/api/cases/{case_id}` | Retrieve a case |
| PATCH | `/api/cases/{case_id}` | Partially update a case |
| DELETE | `/api/cases/{case_id}` | Delete a case |

Allowed dispute types: `non_delivery`, `fake_delivery`, `payment_fraud`, `amount_mismatch`, `other`.

Allowed statuses: `pending`, `investigating`, `resolved`, `rejected`.

## Example case payload

```json
{
  "customer_name": "Rahul Kumar",
  "seller_name": "ABC Electronics",
  "order_id": "ORD-1001",
  "transaction_id": "TXN-5001",
  "dispute_type": "non_delivery",
  "description": "Customer completed payment of 5000 INR but claims that the product was never delivered."
}
```

## Notes
- This is Phase 1, not the complete final product.
- Evidence metadata tables are included; upload and OCR functionality come in later phases.
- Use synthetic data for testing. Do not upload real financial documents until authentication, authorization, retention, and secure storage controls are implemented.
- SQLite `create_all()` is suitable for this starter phase. Add database migrations before frequent schema changes.
