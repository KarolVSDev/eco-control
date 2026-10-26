from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.schemas.gap_report import GapReportResponse
from app.services.gap_report_service import GapReportService
from app.utils.security import current_user


router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/gap", response_model=GapReportResponse)
def gap_report(
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    _=Depends(current_user),
):
    return GapReportService(db).report(start_date, end_date)
