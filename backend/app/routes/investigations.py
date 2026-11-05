from datetime import datetime, timezone
import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.case import Case
from app.models.investigation import CaseInvestigation, CaseInvestigationMessage
from app.schemas.investigation import (
    CaseInvestigationResponse,
    DiscrepancyExplanation,
    InvestigationChatMessageResponse,
    InvestigationChatRequest,
    ObservationItem,
    RecommendedAction,
)
from app.services.investigation_agent import (
    execute_case_investigation,
    handle_investigation_chat,
)
from app.services.llm_client import (
    LLMClientError,
    LLMResponseValidationError,
    LLMTimeoutError,
    LLMUnavailableError,
)
from app.services.timeline import record_timeline_event

router = APIRouter(prefix="/api/cases", tags=["AI Investigation Agent"])


def format_investigation_response(inv: CaseInvestigation) -> CaseInvestigationResponse:
    obs_raw = inv.get_key_observations()
    disc_raw = inv.get_identified_discrepancies()
    recs_raw = inv.get_recommended_actions()
    missing_raw = inv.get_missing_information()
    supporting_ids = inv.get_supporting_evidence_ids()

    return CaseInvestigationResponse(
        id=inv.id,
        case_id=inv.case_id,
        verification_id=inv.verification_id,
        summary=inv.summary,
        key_observations=[ObservationItem(**o) for o in obs_raw],
        identified_discrepancies=[DiscrepancyExplanation(**d) for d in disc_raw],
        missing_information=missing_raw,
        recommended_actions=[RecommendedAction(**r) for r in recs_raw],
        supporting_evidence_ids=supporting_ids,
        related_verification_codes=[d.get("code") for d in disc_raw if isinstance(d, dict) and d.get("code")],
        confidence_explanation=inv.confidence_explanation,
        human_review_status=inv.human_review_status,
        provider_used=inv.provider_used,
        model_used=inv.model_used,
        created_at=inv.created_at,
    )


@router.post(
    "/{case_id}/investigations",
    response_model=CaseInvestigationResponse,
    summary="Start an AI investigation analysis for a case",
)
def start_case_investigation(case_id: str, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    try:
        inv = execute_case_investigation(case, db)
        record_timeline_event(
            db=db,
            case_id=case.case_id,
            event_type="investigation_completed",
            category="investigation",
            title=f"AI Investigation Assessment Generated ({inv.provider_used.upper()})",
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
                "discrepancies_count": len(inv.get_identified_discrepancies()),
            },
            idempotency_key=f"investigation_completed:{inv.id}",
        )
        return format_investigation_response(inv)
    except LLMTimeoutError as te:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"AI investigation timed out: {str(te)}",
        )
    except LLMUnavailableError as ue:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI investigation provider unavailable: {str(ue)}",
        )
    except LLMResponseValidationError as ve:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI investigation emitted invalid structure: {str(ve)}",
        )
    except LLMClientError as ce:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI investigation failed: {str(ce)}",
        )


@router.get(
    "/{case_id}/investigations/latest",
    response_model=CaseInvestigationResponse,
    summary="Get latest AI investigation report for a case",
)
def get_latest_investigation(case_id: str, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    inv = (
        db.query(CaseInvestigation)
        .filter(CaseInvestigation.case_id == case_id)
        .order_by(CaseInvestigation.created_at.desc())
        .first()
    )
    if inv is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No AI investigation has been executed for this case yet.",
        )

    return format_investigation_response(inv)


@router.get(
    "/{case_id}/investigations",
    response_model=list[CaseInvestigationResponse],
    summary="List all historical AI investigations for a case",
)
def get_investigation_history(case_id: str, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    history = (
        db.query(CaseInvestigation)
        .filter(CaseInvestigation.case_id == case_id)
        .order_by(CaseInvestigation.created_at.desc())
        .all()
    )
    return [format_investigation_response(inv) for inv in history]


@router.get(
    "/{case_id}/investigations/{investigation_id}",
    response_model=CaseInvestigationResponse,
    summary="Get a specific AI investigation by ID",
)
def get_investigation_by_id(case_id: str, investigation_id: str, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    inv = (
        db.query(CaseInvestigation)
        .filter(CaseInvestigation.id == investigation_id, CaseInvestigation.case_id == case_id)
        .first()
    )
    if inv is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investigation not found for this case.",
        )

    return format_investigation_response(inv)


@router.post(
    "/{case_id}/investigations/{investigation_id}/chat",
    response_model=InvestigationChatMessageResponse,
    summary="Ask a follow-up question regarding a case investigation",
)
def chat_investigation(
    case_id: str,
    investigation_id: str,
    payload: InvestigationChatRequest,
    db: Session = Depends(get_db),
):
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    inv = (
        db.query(CaseInvestigation)
        .filter(CaseInvestigation.id == investigation_id, CaseInvestigation.case_id == case_id)
        .first()
    )
    if inv is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investigation not found for this case.",
        )

    try:
        assistant_msg = handle_investigation_chat(case, inv, payload.message, db)

        # Record investigator query event
        record_timeline_event(
            db=db,
            case_id=case.case_id,
            event_type="follow_up_submitted",
            category="investigation",
            title="Investigator Follow-Up Query",
            description=payload.message,
            event_timestamp=assistant_msg.created_at,
            actor="investigator",
            related_investigation_id=inv.id,
            metadata={"investigation_id": inv.id},
            idempotency_key=f"chat_message_user:{assistant_msg.id}",
        )

        # Record AI assistant response event
        record_timeline_event(
            db=db,
            case_id=case.case_id,
            event_type="ai_response_generated",
            category="investigation",
            title="AI Investigation Response",
            description=assistant_msg.message,
            event_timestamp=assistant_msg.created_at,
            actor="ai_agent",
            related_investigation_id=inv.id,
            related_evidence_ids=assistant_msg.get_cited_evidence_ids(),
            metadata={"message_id": assistant_msg.id, "investigation_id": inv.id},
            idempotency_key=f"chat_message:{assistant_msg.id}",
        )

        return InvestigationChatMessageResponse(
            id=assistant_msg.id,
            investigation_id=assistant_msg.investigation_id,
            case_id=assistant_msg.case_id,
            sender=assistant_msg.sender,
            message=assistant_msg.message,
            cited_evidence_ids=assistant_msg.get_cited_evidence_ids(),
            created_at=assistant_msg.created_at,
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Follow-up chat failed: {str(err)}",
        )


@router.get(
    "/{case_id}/investigations/{investigation_id}/messages",
    response_model=list[InvestigationChatMessageResponse],
    summary="Get conversation history for an investigation",
)
def get_investigation_messages(
    case_id: str,
    investigation_id: str,
    db: Session = Depends(get_db),
):
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    messages = (
        db.query(CaseInvestigationMessage)
        .filter(CaseInvestigationMessage.investigation_id == investigation_id, CaseInvestigationMessage.case_id == case_id)
        .order_by(CaseInvestigationMessage.created_at.asc())
        .all()
    )

    return [
        InvestigationChatMessageResponse(
            id=m.id,
            investigation_id=m.investigation_id,
            case_id=m.case_id,
            sender=m.sender,
            message=m.message,
            cited_evidence_ids=m.get_cited_evidence_ids(),
            created_at=m.created_at,
        )
        for m in messages
    ]

