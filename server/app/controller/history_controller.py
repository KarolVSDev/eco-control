import csv
import io
import json
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.entities import AnalystPermission, FieldPermission
from app.repository.history_repository import HistoryRepository
from app.utils.security import current_user

router = APIRouter(prefix="/history", tags=["History"])

CSV_COLUMNS = (
    "id",
    "eco_id",
    "eco_code",
    "item",
    "field_key",
    "field_label",
    "old_value",
    "new_value",
    "user_email",
    "user_name",
    "action",
    "created_at",
)


def _authorize_history(db: Session, user):
    if user.role == "admin":
        return set()

    permission = db.scalar(
        select(AnalystPermission).where(
            AnalystPermission.user_email == user.email
        )
    )
    if not permission or not permission.can_view_history:
        raise HTTPException(
            status_code=403,
            detail="Você não possui permissão para visualizar o histórico.",
        )

    permissions = db.scalars(
        select(FieldPermission).where(
            FieldPermission.user_email == user.email
        )
    ).all()
    hidden_fields = set()
    for permission in permissions:
        if permission.can_view is False:
            key = permission.field_key
            hidden_fields.add("group" if key == "group_name" else key)
            hidden_fields.add(key)
    return hidden_fields


def _filtered_snapshot(record, hidden_fields):
    if (
        record.get("action") != "created"
        or record.get("field_key") != "eco"
        or not record.get("new_value")
    ):
        return record

    try:
        snapshot = json.loads(record["new_value"])
    except (TypeError, json.JSONDecodeError):
        return record

    for field in hidden_fields:
        snapshot.pop(field, None)
    record["new_value"] = json.dumps(
        snapshot,
        ensure_ascii=False,
        sort_keys=True,
    )
    return record


def _serialize_history(item, hidden_fields):
    record = {
        column.name: getattr(item, column.name)
        for column in item.__table__.columns
    }
    record["id"] = str(record["id"])
    record["eco_id"] = str(record["eco_id"]) if record["eco_id"] else None
    if record["created_at"]:
        record["created_at"] = record["created_at"].isoformat()
    return _filtered_snapshot(record, hidden_fields)


def _validated_pagination(page: int, page_size: int):
    if page < 1:
        raise HTTPException(status_code=422, detail="page deve ser maior ou igual a 1.")
    if page_size < 1 or page_size > 500:
        raise HTTPException(status_code=422, detail="page_size deve estar entre 1 e 500.")


def _filters(
    date_start,
    date_end,
    user_email,
    field,
    action,
    eco,
    search,
    hidden_fields,
):
    return {
        "date_start": date_start,
        "date_end": date_end,
        "user_email": user_email,
        "field": field,
        "action": action,
        "eco": eco,
        "search": search,
        "hidden_fields": hidden_fields,
    }


def _history_params(
    date_start: datetime | None,
    date_end: datetime | None,
    user_email: str | None,
    field: str | None,
    action: str | None,
    eco: str | None,
    search: str | None,
):
    if date_start and date_end and date_start > date_end:
        raise HTTPException(
            status_code=422,
            detail="date_start não pode ser posterior a date_end.",
        )
    return date_start, date_end, user_email, field, action, eco, search


@router.get("")
def list_history(
    page: int = 1,
    page_size: int = 20,
    date_start: datetime | None = None,
    date_end: datetime | None = None,
    user_email: str | None = None,
    field: str | None = None,
    action: Literal["created", "updated", "deleted"] | None = None,
    eco: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    _validated_pagination(page, page_size)
    _history_params(
        date_start, date_end, user_email, field, action, eco, search
    )
    hidden_fields = _authorize_history(db, user)
    items, total = HistoryRepository(db).list(
        page=page,
        page_size=page_size,
        **_filters(
            date_start,
            date_end,
            user_email,
            field,
            action,
            eco,
            search,
            hidden_fields,
        ),
    )
    return {
        "items": [
            _serialize_history(item, hidden_fields)
            for item in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/export")
def export_history(
    date_start: datetime | None = None,
    date_end: datetime | None = None,
    user_email: str | None = None,
    field: str | None = None,
    action: Literal["created", "updated", "deleted"] | None = None,
    eco: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    _history_params(
        date_start, date_end, user_email, field, action, eco, search
    )
    hidden_fields = _authorize_history(db, user)
    filters = _filters(
        date_start,
        date_end,
        user_email,
        field,
        action,
        eco,
        search,
        hidden_fields,
    )
    repository = HistoryRepository(db)

    def csv_rows():
        buffer = io.StringIO(newline="")
        writer = csv.writer(buffer)
        writer.writerow(CSV_COLUMNS)
        yield "\ufeff" + buffer.getvalue()

        for item in repository.iter_filtered(**filters):
            record = _serialize_history(item, hidden_fields)
            buffer.seek(0)
            buffer.truncate(0)
            writer.writerow([record.get(column) for column in CSV_COLUMNS])
            yield buffer.getvalue()

    return StreamingResponse(
        csv_rows(),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="eco-history.csv"'
        },
    )
