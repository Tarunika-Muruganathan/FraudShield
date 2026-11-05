from datetime import datetime, timezone
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.document_data import EvidenceDocumentData
from app.models.evidence import Evidence
from app.schemas.document_data import (
    DeliveryIntelligence,
    EvidenceDocumentDataResponse,
    ExtractedDataResponse,
    OrderIntelligence,
    PaymentIntelligence,
)
from app.services.extractor import extract_document_intelligence
from app.services.ocr import OcrProcessingError, process_document_ocr
from app.services.storage import get_evidence_file_path

router = APIRouter(prefix="/api/evidence", tags=["Document Intelligence & OCR"])


@router.post(
    "/{evidence_id}/process-ocr",
    response_model=EvidenceDocumentDataResponse,
    summary="Process OCR and extract document intelligence from evidence",
)
def process_evidence_ocr(
    evidence_id: str,
    force: bool = Query(False, description="Force re-processing if already completed"),
    db: Session = Depends(get_db),
):
    evidence = db.query(Evidence).filter(Evidence.evidence_id == evidence_id).first()
    if evidence is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence not found",
        )

    # Check for existing document data
    doc_data = (
        db.query(EvidenceDocumentData)
        .filter(EvidenceDocumentData.evidence_id == evidence_id)
        .first()
    )

    # Prevent duplicate processing unless force=True
    if doc_data and doc_data.ocr_status == "completed" and not force:
        return doc_data

    if doc_data is None:
        doc_data = EvidenceDocumentData(
            id=str(uuid.uuid4()),
            evidence_id=evidence_id,
            ocr_status="processing",
        )
        db.add(doc_data)
        db.commit()
        db.refresh(doc_data)
    else:
        doc_data.ocr_status = "processing"
        db.commit()

    try:
        file_path = get_evidence_file_path(evidence.stored_filename)
        raw_text = process_document_ocr(file_path, evidence.filename)

        # Extract structured intelligence from OCR text
        extracted_fields = extract_document_intelligence(raw_text)

        # Update evidence model's extracted_text
        evidence.extracted_text = raw_text

        # Update document data model
        doc_data.raw_text = raw_text
        doc_data.ocr_status = "completed" if raw_text.strip() else "unreadable"
        doc_data.ocr_error = None if raw_text.strip() else "Document contains no readable text or characters."

        # Payment fields
        doc_data.transaction_id = extracted_fields.get("transaction_id")
        doc_data.payment_amount = extracted_fields.get("payment_amount")
        doc_data.currency = extracted_fields.get("currency")
        doc_data.payment_date = extracted_fields.get("payment_date")
        doc_data.payment_status = extracted_fields.get("payment_status")
        doc_data.sender_name = extracted_fields.get("sender_name")
        doc_data.receiver_name = extracted_fields.get("receiver_name")
        doc_data.payment_reference = extracted_fields.get("payment_reference")

        # Order fields
        doc_data.order_id = extracted_fields.get("order_id")
        doc_data.order_date = extracted_fields.get("order_date")
        doc_data.product_description = extracted_fields.get("product_description")
        doc_data.order_amount = extracted_fields.get("order_amount")
        doc_data.customer_information = extracted_fields.get("customer_information")

        # Delivery fields
        doc_data.tracking_number = extracted_fields.get("tracking_number")
        doc_data.delivery_date = extracted_fields.get("delivery_date")
        doc_data.delivery_status = extracted_fields.get("delivery_status")
        doc_data.recipient_information = extracted_fields.get("recipient_information")
        doc_data.delivery_address = extracted_fields.get("delivery_address")

        doc_data.processed_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(doc_data)
        return doc_data

    except OcrProcessingError as ocr_err:
        doc_data.ocr_status = "unreadable"
        doc_data.ocr_error = str(ocr_err)
        doc_data.processed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(doc_data)
        return doc_data

    except Exception as err:
        doc_data.ocr_status = "failed"
        doc_data.ocr_error = f"Unexpected OCR processing error: {str(err)}"
        doc_data.processed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(doc_data)
        return doc_data


@router.get(
    "/{evidence_id}/ocr",
    response_model=EvidenceDocumentDataResponse,
    summary="Get OCR result and extracted document intelligence",
)
def get_evidence_ocr(evidence_id: str, db: Session = Depends(get_db)):
    evidence = db.query(Evidence).filter(Evidence.evidence_id == evidence_id).first()
    if evidence is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence not found",
        )

    doc_data = (
        db.query(EvidenceDocumentData)
        .filter(EvidenceDocumentData.evidence_id == evidence_id)
        .first()
    )

    if doc_data is None:
        # Return pending placeholder without saving to DB yet
        return EvidenceDocumentDataResponse(
            id=str(uuid.uuid4()),
            evidence_id=evidence_id,
            ocr_status="pending",
            ocr_error=None,
            raw_text=evidence.extracted_text,
            processed_at=None,
        )

    return doc_data


@router.get(
    "/{evidence_id}/extracted-data",
    response_model=ExtractedDataResponse,
    summary="Retrieve extracted structured information for an evidence file",
)
def get_evidence_extracted_data(evidence_id: str, db: Session = Depends(get_db)):
    evidence = db.query(Evidence).filter(Evidence.evidence_id == evidence_id).first()
    if evidence is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence not found",
        )

    doc_data = (
        db.query(EvidenceDocumentData)
        .filter(EvidenceDocumentData.evidence_id == evidence_id)
        .first()
    )

    if doc_data is None:
        return ExtractedDataResponse(
            evidence_id=evidence_id,
            ocr_status="pending",
            payment=PaymentIntelligence(),
            order=OrderIntelligence(),
            delivery=DeliveryIntelligence(),
            processed_at=None,
        )

    return ExtractedDataResponse(
        evidence_id=evidence_id,
        ocr_status=doc_data.ocr_status,
        payment=PaymentIntelligence(
            transaction_id=doc_data.transaction_id,
            payment_amount=doc_data.payment_amount,
            currency=doc_data.currency,
            payment_date=doc_data.payment_date,
            payment_status=doc_data.payment_status,
            sender_name=doc_data.sender_name,
            receiver_name=doc_data.receiver_name,
            payment_reference=doc_data.payment_reference,
        ),
        order=OrderIntelligence(
            order_id=doc_data.order_id,
            order_date=doc_data.order_date,
            product_description=doc_data.product_description,
            order_amount=doc_data.order_amount,
            customer_information=doc_data.customer_information,
        ),
        delivery=DeliveryIntelligence(
            tracking_number=doc_data.tracking_number,
            delivery_date=doc_data.delivery_date,
            delivery_status=doc_data.delivery_status,
            recipient_information=doc_data.recipient_information,
            delivery_address=doc_data.delivery_address,
        ),
        processed_at=doc_data.processed_at,
    )

