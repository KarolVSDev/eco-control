from datetime import date

from pydantic import BaseModel


class GapReportItem(BaseModel):
    id: str
    eco: str | None
    eco_type: str | None
    az_eco_creation_date: date | None
    effective_date: date | None
    approval_date: date
    gap_14d: int | None
    gap_14d_note: str | None
    requires_gap_14d_note: bool


class GapReportResponse(BaseModel):
    start_date: date
    end_date: date
    total: int
    items: list[GapReportItem]
