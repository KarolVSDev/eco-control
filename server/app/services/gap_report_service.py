from fastapi import HTTPException

from app.repository.gap_report_repository import GapReportRepository
from app.schemas.gap_report import GapReportItem, GapReportResponse
from app.utils.eco_calculations import compute_eco_fields, normalize_status


class GapReportService:
    def __init__(self, db):
        self.repo = GapReportRepository(db)

    def report(self, start_date, end_date):
        if start_date > end_date:
            raise HTTPException(
                status_code=422,
                detail="Data inicial não pode ser posterior à data final.",
            )

        items = []
        for eco in self.repo.list_in_period(start_date, end_date):
            # Reuse Python normalization, including whitespace handled by str.split().
            if normalize_status(eco.status) != "RELEASED":
                continue
            computed = compute_eco_fields(eco)
            items.append(GapReportItem(
                id=str(eco.id),
                origin_eco=eco.hz_in_kr_eco_1,
                # The automation persists Title in eco.title. Historical matrix
                # imports already store the BM description in change_reason_az,
                # so keep it as a read-only fallback for the report.
                title=eco.title or eco.change_reason_az,
                eco_type=eco.eco_type,
                effective_date=eco.effective_date,
                eco=eco.eco,
                az_eco_creation_date=eco.az_eco_creation_date,
                approval_date=eco.second_aprov_rd_finish_1,
                gap_14d=computed["gap_14d"],
                gap_14d_note=eco.gap_14d_note,
                requires_gap_14d_note=computed["requires_gap_14d_note"],
            ))

        return GapReportResponse(
            start_date=start_date, end_date=end_date, total=len(items), items=items,
        )
