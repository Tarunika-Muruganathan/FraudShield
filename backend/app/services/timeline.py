from datetime import datetime, timezone
import json
from typing import Any
import uuid

from sqlalchemy.orm import Session

from app.models.case import Case
from app.models.timeline import TimelineEvent
from app.schemas.timeline import TimelineEventResponse


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def format_timeline_event_response(event: TimelineEvent) -> TimelineEventResponse:
    return TimelineEventResponse(
        event_id=event.event_id,
        case_id=event.case_id,
        event_type=event.event_type,
        category=event.category,
        title=event.title,
        description=event.description,
        event_timestamp=event.event_timestamp,
        recorded_at=event.recorded_at,
        actor=event.actor,
        related_evidence_ids=event.get_related_evidence_ids(),
        related_verification_id=event.related_verification_id,
        related_investigation_id=event.related_investigation_id,
        metadata=event.get_metadata(),
    )


def record_timeline_event(
    db: Session,
    case_id: str,
    event_type: str,
    category: str,
    title: str,
    description: str,
    event_timestamp: datetime | None = None,
    actor: str | None = None,
    related_evidence_ids: list[str] | None = None,
    related_verification_id: str | None = None,
    related_investigation_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    idempotency_key: str | None = None,
    commit: bool = True,
) -> TimelineEvent:
    """
    Record an append-only timeline event with deterministic duplicate prevention.
    """
    if idempotency_key:
        existing = (
            db.query(TimelineEvent)
            .filter(
                TimelineEvent.case_id == case_id,
                TimelineEvent.idempotency_key == idempotency_key,
            )
            .first()
        )
        if existing:
            return existing

    event = TimelineEvent(
        event_id=str(uuid.uuid4()),
        case_id=case_id,
        idempotency_key=idempotency_key,
        event_type=event_type,
        category=category,
        title=title,
        description=description,
        event_timestamp=event_timestamp,
        recorded_at=utc_now(),
        actor=actor,
        related_evidence_ids=json.dumps(related_evidence_ids or []),
        related_verification_id=related_verification_id,
        related_investigation_id=related_investigation_id,
        metadata_json=json.dumps(metadata or {}),
    )
    db.add(event)
    if commit:
        db.commit()
        db.refresh(event)
    return event


def sync_case_timeline(case: Case, db: Session) -> None:
    """
    Idempotently reconstructs historical events supported by actual existing database records.
    Never fabricates missing data, timestamps or status transitions.
    """
    needs_commit = False

    # 1. Case Creation Event
    case_create_key = f"case_created:{case.case_id}"
    if not db.query(TimelineEvent).filter(TimelineEvent.case_id == case.case_id, TimelineEvent.idempotency_key == case_create_key).first():
        record_timeline_event(
            db=db,
            case_id=case.case_id,
            event_type="case_created",
            category="case",
            title="Case Registered",
            description=f"Case opened for Order {case.order_id} under dispute category '{case.dispute_type}'.",
            event_timestamp=case.created_at,
            actor="investigator",
            metadata={
                "order_id": case.order_id,
                "dispute_type": case.dispute_type,
                "customer_name": case.customer_name,
                "seller_name": case.seller_name,
            },
            idempotency_key=case_create_key,
            commit=False,
        )
        needs_commit = True

    # 2. Evidence Upload and Document Intelligence Events
    for ev in case.evidence:
        ev_upload_key = f"evidence_uploaded:{ev.evidence_id}"
        if not db.query(TimelineEvent).filter(TimelineEvent.case_id == case.case_id, TimelineEvent.idempotency_key == ev_upload_key).first():
            record_timeline_event(
                db=db,
                case_id=case.case_id,
                event_type="evidence_uploaded",
                category="evidence",
                title=f"Evidence Uploaded: {ev.filename}",
                description=f"Evidence file '{ev.filename}' ({ev.file_size} bytes) registered in evidence locker.",
                event_timestamp=ev.uploaded_at,
                actor="investigator",
                related_evidence_ids=[ev.evidence_id],
                metadata={
                    "evidence_id": ev.evidence_id,
                    "filename": ev.filename,
                    "file_size": ev.file_size,
                    "content_type": ev.content_type,
                    "sha256_hash": ev.sha256_hash,
                },
                idempotency_key=ev_upload_key,
                commit=False,
            )
            needs_commit = True

        if ev.document_data:
            doc = ev.document_data
            if doc.ocr_status == "completed":
                ocr_key = f"ocr_completed:{ev.evidence_id}"
                if not db.query(TimelineEvent).filter(TimelineEvent.case_id == case.case_id, TimelineEvent.idempotency_key == ocr_key).first():
                    fields_found = []
                    if doc.payment_amount:
                        fields_found.append("payment_amount")
                    if doc.transaction_id:
                        fields_found.append("transaction_id")
                    if doc.order_id:
                        fields_found.append("order_id")
                    if doc.tracking_number:
                        fields_found.append("tracking_number")
                    if doc.delivery_status:
                        fields_found.append("delivery_status")

                    record_timeline_event(
                        db=db,
                        case_id=case.case_id,
                        event_type="ocr_completed",
                        category="ocr",
                        title=f"OCR Extraction Completed: {ev.filename}",
                        description=f"Document text extracted and parsed into structured fields. Identified: {', '.join(fields_found) if fields_found else 'document text'}.",
                        event_timestamp=doc.processed_at or ev.uploaded_at,
                        actor="ocr_engine",
                        related_evidence_ids=[ev.evidence_id],
                        metadata={
                            "evidence_id": ev.evidence_id,
                            "filename": ev.filename,
                            "ocr_status": "completed",
                            "fields_extracted": fields_found,
                        },
                        idempotency_key=ocr_key,
                        commit=False,
                    )
                    needs_commit = True

            elif doc.ocr_status in ("unreadable", "failed"):
                ocr_fail_key = f"ocr_failed:{ev.evidence_id}"
                if not db.query(TimelineEvent).filter(TimelineEvent.case_id == case.case_id, TimelineEvent.idempotency_key == ocr_fail_key).first():
                    record_timeline_event(
                        db=db,
                        case_id=case.case_id,
                        event_type="ocr_failed",
                        category="ocr",
                        title=f"OCR Processing {doc.ocr_status.capitalize()}: {ev.filename}",
                        description=doc.ocr_error or f"Document processing finished with status: {doc.ocr_status}",
                        event_timestamp=doc.processed_at or ev.uploaded_at,
                        actor="ocr_engine",
                        related_evidence_ids=[ev.evidence_id],
                        metadata={
                            "evidence_id": ev.evidence_id,
                            "filename": ev.filename,
                            "ocr_status": doc.ocr_status,
                            "error": doc.ocr_error,
                        },
                        idempotency_key=ocr_fail_key,
                        commit=False,
                    )
                    needs_commit = True

    # 3. Deterministic Fraud Verification Events
    for ver in case.verifications:
        ver_key = f"verification_completed:{ver.id}"
        if not db.query(TimelineEvent).filter(TimelineEvent.case_id == case.case_id, TimelineEvent.idempotency_key == ver_key).first():
            disc_count = len(ver.get_discrepancies_list())
            missing_count = len(ver.get_missing_evidence_list())
            record_timeline_event(
                db=db,
                case_id=case.case_id,
                event_type="verification_completed",
                category="verification",
                title=f"Verification Assessment: Risk {ver.risk_level} ({ver.risk_score}/100)",
                description=ver.summary,
                event_timestamp=ver.verified_at,
                actor="verification_engine",
                related_verification_id=ver.id,
                metadata={
                    "verification_id": ver.id,
                    "risk_level": ver.risk_level,
                    "risk_score": ver.risk_score,
                    "discrepancies_count": disc_count,
                    "missing_evidence_count": missing_count,
                },
                idempotency_key=ver_key,
                commit=False,
            )
            needs_commit = True

    # 4. AI Investigation Events and Q&A Messages
    for inv in case.investigations:
        inv_key = f"investigation_completed:{inv.id}"
        if not db.query(TimelineEvent).filter(TimelineEvent.case_id == case.case_id, TimelineEvent.idempotency_key == inv_key).first():
            record_timeline_event(
                db=db,
                case_id=case.case_id,
                event_type="investigation_completed",
                category="investigation",
                title=f"AI Investigation Completed ({inv.provider_used.upper()})",
                description=inv.summary,
                event_timestamp=inv.created_at,
                actor="ai_agent",
                related_investigation_id=inv.id,
                related_evidence_ids=inv.get_supporting_evidence_ids(),
                metadata={
                    "investigation_id": inv.id,
                    "provider_used": inv.provider_used,
                    "model_used": inv.model_used,
                    "human_review_status": inv.human_review_status,
                },
                idempotency_key=inv_key,
                commit=False,
            )
            needs_commit = True

        for msg in inv.messages:
            msg_key = f"chat_message:{msg.id}"
            if not db.query(TimelineEvent).filter(TimelineEvent.case_id == case.case_id, TimelineEvent.idempotency_key == msg_key).first():
                is_user = msg.sender in ("user", "investigator")
                record_timeline_event(
                    db=db,
                    case_id=case.case_id,
                    event_type="follow_up_submitted" if is_user else "ai_response_generated",
                    category="investigation",
                    title="Investigator Follow-Up Query" if is_user else "AI Investigation Response",
                    description=msg.message,
                    event_timestamp=msg.created_at,
                    actor="investigator" if is_user else "ai_agent",
                    related_investigation_id=inv.id,
                    related_evidence_ids=msg.get_cited_evidence_ids(),
                    metadata={
                        "message_id": msg.id,
                        "investigation_id": inv.id,
                        "sender": msg.sender,
                    },
                    idempotency_key=msg_key,
                    commit=False,
                )
                needs_commit = True

    if needs_commit:
        db.commit()


def get_case_timeline_events(
    case: Case,
    db: Session,
    category: str | None = None,
    sort: str = "desc",
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[TimelineEvent], int]:
    """
    Retrieves chronological timeline events with deterministic tie-breaking and pagination.
    """
    # Sync legacy / pre-existing DB records first
    sync_case_timeline(case, db)

    query = db.query(TimelineEvent).filter(TimelineEvent.case_id == case.case_id)

    if category:
        query = query.filter(TimelineEvent.category == category.lower())

    total_count = query.count()

    if sort == "asc":
        # Ascending: oldest first; events with null timestamp placed at the end deterministically
        query = query.order_by(
            TimelineEvent.event_timestamp.is_(None),
            TimelineEvent.event_timestamp.asc(),
            TimelineEvent.recorded_at.asc(),
            TimelineEvent.event_id.asc(),
        )
    else:
        # Descending: newest first; events with null timestamp placed at the end deterministically
        query = query.order_by(
            TimelineEvent.event_timestamp.is_(None),
            TimelineEvent.event_timestamp.desc(),
            TimelineEvent.recorded_at.desc(),
            TimelineEvent.event_id.desc(),
        )

    events = query.offset(offset).limit(limit).all()
    return events, total_count

