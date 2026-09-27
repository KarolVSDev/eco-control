import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.repository.history_repository import HistoryRepository
from app.repository.permission_repository import PermissionRepository
from app.utils.security import current_user

router = APIRouter(prefix='/history', tags=['History'])


def require_history_access(db: Session = Depends(get_db), user=Depends(current_user)):
    if user.role == 'admin':
        return user
    general = PermissionRepository(db).get_general(user.email)
    if general is not None and general.can_view_history is False:
        raise HTTPException(403, 'Sem permissão para visualizar o histórico')
    return user


def _row_to_dict(x):
    data = {c.name: getattr(x, c.name) for c in x.__table__.columns}
    data['id'] = str(data['id'])
    data['eco_id'] = str(data['eco_id']) if data['eco_id'] else None
    return data


@router.get('')
def list_history(
    page: int = 1,
    page_size: int = 20,
    date_start: datetime | None = None,
    date_end: datetime | None = None,
    user_email: str | None = None,
    field: str | None = None,
    eco: str | None = None,
    action: str | None = None,
    db: Session = Depends(get_db),
    _=Depends(require_history_access),
):
    items, total = HistoryRepository(db).list(page, page_size, date_start, date_end, user_email, field, eco, action)
    return {'items': [_row_to_dict(x) for x in items], 'total': total, 'page': page, 'page_size': page_size}


@router.get('/actions')
def list_actions(db: Session = Depends(get_db), _=Depends(require_history_access)):
    return HistoryRepository(db).actions()


@router.get('/export')
def export_history(
    date_start: datetime | None = None,
    date_end: datetime | None = None,
    user_email: str | None = None,
    field: str | None = None,
    eco: str | None = None,
    action: str | None = None,
    db: Session = Depends(get_db),
    _=Depends(require_history_access),
):
    items, _total = HistoryRepository(db).list(1, 10000, date_start, date_end, user_email, field, eco, action)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(['Data/Hora', 'Usuário', 'ECO', 'Item', 'Ação', 'Campo', 'Valor anterior', 'Valor novo'])
    for x in items:
        writer.writerow([
            x.created_at.isoformat() if x.created_at else '',
            x.user_name or x.user_email or '',
            x.eco_code or '',
            x.item if x.item is not None else '',
            x.action or '',
            x.field_label or '',
            x.old_value or '',
            x.new_value or '',
        ])
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="historico.csv"'},
    )
