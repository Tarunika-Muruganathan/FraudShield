from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.case import Case
from app.schemas.timeline import TimelineEventResponse
from app.services.timeline import format_timeline_event_response, get_case_timeline_events

router = APIRouter(prefix="/api/cases", tags=["Investigation Timeline"])


@router.get(
    "/{case_id}/timeline",
    response_model=list[TimelineEventResponse],
    summary="Get chronological investigation timeline for a case",
)
def get_case_timeline(
    case_id: str,
    response: Response,
    category: str | None = Query(None, description="Filter by event category (case, evidence, ocr, verification, investigation, human_review)"),
    sort: str = Query("desc", description="Chronological sorting: 'asc' or 'desc'"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of events to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db),
):
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    sort_lower = sort.lower().strip()
    if sort_lower not in ("asc", "desc"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid sort order. Permitted values are 'asc' or 'desc'.",
        )

    valid_categories = {"case", "evidence", "ocr", "verification", "investigation", "human_review"}
    if category and category.lower().strip() not in valid_categories:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid category filter. Permitted values are: {', '.join(sorted(valid_categories))}",
        )

    events, total_count = get_case_timeline_events(
        case=case,
        db=db,
        category=category.lower().strip() if category else None,
        sort=sort_lower,
        limit=limit,
        offset=offset,
    )

    response.headers["X-Total-Count"] = str(total_count)
    return [format_timeline_event_response(ev) for ev in events]

