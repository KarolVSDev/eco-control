from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.models.entities import EcoHistory


class HistoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, history: EcoHistory):
        self.db.add(history)

    def _filtered_query(
        self,
        date_start=None,
        date_end=None,
        user_email=None,
        field=None,
        action=None,
        eco=None,
        search=None,
        hidden_fields=(),
    ):
        query = select(EcoHistory)
        filters = []

        if date_start:
            filters.append(EcoHistory.created_at >= date_start)
        if date_end:
            filters.append(EcoHistory.created_at <= date_end)
        if user_email:
            pattern = f"%{user_email.strip()}%"
            filters.append(
                or_(
                    EcoHistory.user_email.ilike(pattern),
                    EcoHistory.user_name.ilike(pattern),
                )
            )
        if field:
            pattern = f"%{field.strip()}%"
            filters.append(
                or_(
                    EcoHistory.field_key.ilike(pattern),
                    EcoHistory.field_label.ilike(pattern),
                )
            )
        if action:
            filters.append(EcoHistory.action == action)
        if eco:
            filters.append(EcoHistory.eco_code.ilike(f"%{eco.strip()}%"))
        if search:
            pattern = f"%{search.strip()}%"
            content_match = or_(
                EcoHistory.old_value.ilike(pattern),
                EcoHistory.new_value.ilike(pattern),
            )
            if hidden_fields:
                content_match = and_(
                    ~and_(
                        EcoHistory.action == "created",
                        EcoHistory.field_key == "eco",
                    ),
                    content_match,
                )
            filters.append(
                or_(
                    EcoHistory.eco_code.ilike(pattern),
                    EcoHistory.user_email.ilike(pattern),
                    EcoHistory.user_name.ilike(pattern),
                    EcoHistory.field_key.ilike(pattern),
                    EcoHistory.field_label.ilike(pattern),
                    content_match,
                )
            )
        if hidden_fields:
            filters.append(~EcoHistory.field_key.in_(hidden_fields))

        if filters:
            query = query.where(*filters)
        return query

    def list(
        self,
        page=1,
        page_size=20,
        date_start=None,
        date_end=None,
        user_email=None,
        field=None,
        action=None,
        eco=None,
        search=None,
        hidden_fields=(),
    ):
        query = self._filtered_query(
            date_start=date_start,
            date_end=date_end,
            user_email=user_email,
            field=field,
            action=action,
            eco=eco,
            search=search,
            hidden_fields=hidden_fields,
        )
        count_query = select(func.count()).select_from(
            query.order_by(None).subquery()
        )
        total = self.db.scalar(count_query) or 0
        items = self.db.scalars(
            query.order_by(
                EcoHistory.created_at.desc(),
                EcoHistory.id.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
        return items, total

    def iter_filtered(self, **filters):
        query = self._filtered_query(**filters)
        result = self.db.scalars(
            query.order_by(
                EcoHistory.created_at.desc(),
                EcoHistory.id.desc(),
            ).execution_options(yield_per=500)
        )
        yield from result
