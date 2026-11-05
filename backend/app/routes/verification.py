from datetime import datetime, timezone
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.case import Case
from app.models.evidence import Evidence
from app.models.verification import CaseVerification
from app.schemas.verification import (
    CaseVerificationResponse,
    DiscrepancyItem,
    MatchItem,
    MissingEvidenceItem,
)
from app.services.verification_engine import run_case_verification

router = APIRouter(prefix="/api/cases", tags=["Fraud Verification Engine"])


def format_verification_response(ver: CaseVerification) -> CaseVerificationResponse:
    discrepancies_raw = ver.get_discrepancies_list()
    matches_raw = ver.get_matches_list()
    missing_raw = ver.get_missing_evidence_list()

    return CaseVerificationResponse(
        id=ver.id,
        case_id=ver.case_id,
        risk_score=ver.risk_score,
        risk_level=ver.risk_level,
        summary=ver.summary,
        discrepancies=[DiscrepancyItem(**d) for d in discrepancies_raw],
        matches=[MatchItem(**m) for m in matches_raw],
        missing_evidence=[MissingEvidenceItem(**me) for me in missing_raw],
        verified_at=ver.verified_at,
    )


@router.post(
    "/{case_id}/verify",
    response_model=CaseVerificationResponse,
    summary="Run deterministic fraud verification engine across case evidence",
)
def verify_case(case_id: str, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    evidence_items = (
        db.query(Evidence)
        .filter(Evidence.case_id == case_id)
        .all()
    )

    assessment = run_case_verification(case, evidence_items)

    new_ver = CaseVerification(
        id=str(uuid.uuid4()),
        case_id=case_id,
        risk_score=assessment["risk_score"],
        risk_level=assessment["risk_level"],
        summary=assessment["summary"],
        discrepancies=json.dumps(assessment["discrepancies"]),
        matches=json.dumps(assessment["matches"]),
        missing_evidence=json.dumps(assessment["missing_evidence"]),
        verified_at=datetime.now(timezone.utc),
    )
    db.add(new_ver)
    db.commit()
    db.refresh(new_ver)

    return format_verification_response(new_ver)


@router.get(
    "/{case_id}/verification",
    response_model=CaseVerificationResponse,
    summary="Get latest fraud verification assessment for a case",
)
def get_latest_case_verification(case_id: str, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    ver = (
        db.query(CaseVerification)
        .filter(CaseVerification.case_id == case_id)
        .order_by(CaseVerification.verified_at.desc())
        .first()
    )
    if ver is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No verification assessment has been run for this case yet.",
        )

    return format_verification_response(ver)


@router.get(
    "/{case_id}/verifications",
    response_model=list[CaseVerificationResponse],
    summary="Get historical verification assessments for a case",
)
def get_case_verification_history(case_id: str, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    history = (
        db.query(CaseVerification)
        .filter(CaseVerification.case_id == case_id)
        .order_by(CaseVerification.verified_at.desc())
        .all()
    )

    return [format_verification_response(v) for v in history]

