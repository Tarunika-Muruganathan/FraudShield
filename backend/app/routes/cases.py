from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.case import Case
from app.schemas.case import CaseCreate, CaseResponse, CaseUpdate
from app.services.storage import delete_stored_file

router = APIRouter(prefix="/api/cases", tags=["Case Management"])


@router.post("/", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
def create_case(case_data: CaseCreate, db: Session = Depends(get_db)):
    new_case = Case(**case_data.model_dump())
    db.add(new_case)
    db.commit()
    db.refresh(new_case)
    return new_case


@router.get("/", response_model=list[CaseResponse])
def get_all_cases(db: Session = Depends(get_db)):
    return db.query(Case).order_by(Case.created_at.desc()).all()


@router.get("/{case_id}", response_model=CaseResponse)
def get_case(case_id: str, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.patch("/{case_id}", response_model=CaseResponse)
def update_case(case_id: str, case_data: CaseUpdate, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")

    for field_name, value in case_data.model_dump(exclude_unset=True).items():
        setattr(case, field_name, value)

    db.commit()
    db.refresh(case)
    return case


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_case(case_id: str, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")

    # Clean up associated physical evidence files before deleting case
    for item in case.evidence:
        delete_stored_file(item.stored_filename)

    db.delete(case)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
