from sqlalchemy import select

from app.models.entities import Eco


class GapReportRepository:
    def __init__(self, db):
        self.db = db

    def list_in_period(self, start_date, end_date):
        return self.db.scalars(
            select(Eco)
            .where(
                Eco.second_aprov_rd_finish_1 >= start_date,
                Eco.second_aprov_rd_finish_1 <= end_date,
            )
            .order_by(
                Eco.second_aprov_rd_finish_1.asc(),
                Eco.eco.asc().nulls_last(),
                Eco.id.asc(),
            )
        ).all()
