from datetime import date

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.schemas.gap_report import GapReportResponse
from app.services.gap_report_service import GapReportService
from app.services.gap_report_export_service import GapReportExportService
from app.services.gap_report_export_service import GapReportExportService
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


@router.get("/gap/export")
def export_gap_report(
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    _=Depends(current_user),
):
    content = GapReportExportService(db).export(start_date, end_date)
    filename = f"relatorio_gap_{start_date.isoformat()}_{end_date.isoformat()}.xlsx"
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/gap/export")
def export_gap_report(
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    _=Depends(current_user),
):
    content = GapReportExportService(db).export(start_date, end_date)
    filename = f"relatorio_gap_{start_date.isoformat()}_{end_date.isoformat()}.xlsx"
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
