from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.case import Case
from app.models.evidence import Evidence
from app.schemas.evidence import EvidenceResponse
from app.services.storage import (
    delete_stored_file,
    get_evidence_file_path,
    save_evidence_file,
)

router = APIRouter(tags=["Evidence Management"])


@router.post(
    "/api/cases/{case_id}/evidence/",
    response_model=EvidenceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload evidence file for a case",
)
async def upload_evidence(
    case_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    clean_filename, stored_filename, sha256_hash, file_size, content_type = (
        await save_evidence_file(file)
    )

    try:
        new_evidence = Evidence(
            case_id=case_id,
            filename=clean_filename,
            stored_filename=stored_filename,
            content_type=content_type,
            file_size=file_size,
            sha256_hash=sha256_hash,
            extracted_text=None,
        )
        db.add(new_evidence)
        db.commit()
        db.refresh(new_evidence)
        return new_evidence
    except Exception:
        delete_stored_file(stored_filename)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record evidence in database.",
        )


@router.get(
    "/api/cases/{case_id}/evidence/",
    response_model=list[EvidenceResponse],
    summary="List all evidence for a case",
)
def get_case_evidence(case_id: str, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    return (
        db.query(Evidence)
        .filter(Evidence.case_id == case_id)
        .order_by(Evidence.uploaded_at.desc())
        .all()
    )


@router.get(
    "/api/evidence/{evidence_id}",
    response_model=EvidenceResponse,
    summary="Get evidence metadata",
)
def get_evidence_metadata(evidence_id: str, db: Session = Depends(get_db)):
    evidence = db.query(Evidence).filter(Evidence.evidence_id == evidence_id).first()
    if evidence is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence not found",
        )
    return evidence


@router.get(
    "/api/evidence/{evidence_id}/download",
    summary="Download evidence file",
)
def download_evidence(evidence_id: str, db: Session = Depends(get_db)):
    evidence = db.query(Evidence).filter(Evidence.evidence_id == evidence_id).first()
    if evidence is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence not found",
        )

    file_path = get_evidence_file_path(evidence.stored_filename)
    return FileResponse(
        path=str(file_path),
        filename=evidence.filename,
        media_type=evidence.content_type or "application/octet-stream",
    )


@router.delete(
    "/api/evidence/{evidence_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete evidence and remove physical file",
)
def delete_evidence(evidence_id: str, db: Session = Depends(get_db)):
    evidence = db.query(Evidence).filter(Evidence.evidence_id == evidence_id).first()
    if evidence is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence not found",
        )

    # Delete physical file from disk
    delete_stored_file(evidence.stored_filename)

    db.delete(evidence)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

