from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.case import Case
from app.schemas.case import CaseCreate, CaseResponse, CaseUpdate
from app.services.storage import delete_stored_file
from app.services.timeline import record_timeline_event

router = APIRouter(prefix="/api/cases", tags=["Case Management"])


@router.post("/", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
def create_case(case_data: CaseCreate, db: Session = Depends(get_db)):
    new_case = Case(**case_data.model_dump())
    db.add(new_case)
    db.commit()
    db.refresh(new_case)

    record_timeline_event(
        db=db,
        case_id=new_case.case_id,
        event_type="case_created",
        category="case",
        title="Case Registered",
        description=f"Case opened for Order {new_case.order_id} (Dispute type: {new_case.dispute_type}).",
        event_timestamp=new_case.created_at,
        actor="investigator",
        metadata={
            "order_id": new_case.order_id,
            "dispute_type": new_case.dispute_type,
            "customer_name": new_case.customer_name,
            "seller_name": new_case.seller_name,
        },
        idempotency_key=f"case_created:{new_case.case_id}",
    )
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

    old_status = case.status
    update_dict = case_data.model_dump(exclude_unset=True)
    new_status = update_dict.get("status")

    for field_name, value in update_dict.items():
        setattr(case, field_name, value)

    db.commit()
    db.refresh(case)

    if new_status and new_status != old_status:
        record_timeline_event(
            db=db,
            case_id=case.case_id,
            event_type="case_status_changed",
            category="case",
            title=f"Case Status Changed: {old_status} -> {new_status}",
            description=f"Case status transitioned from '{old_status}' to '{new_status}' by investigator.",
            event_timestamp=case.updated_at,
            actor="investigator",
            metadata={"old_status": old_status, "new_status": new_status},
        )
    elif update_dict:
        record_timeline_event(
            db=db,
            case_id=case.case_id,
            event_type="case_updated",
            category="case",
            title="Case Information Updated",
            description=f"Fields modified: {', '.join(update_dict.keys())}",
            event_timestamp=case.updated_at,
            actor="investigator",
            metadata={"updated_fields": list(update_dict.keys())},
        )

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
