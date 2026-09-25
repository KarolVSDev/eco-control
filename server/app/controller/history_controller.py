from datetime import datetime
from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.entities import AnalystPermission,FieldPermission
from app.repository.history_repository import HistoryRepository
from app.utils.security import current_user
router=APIRouter(prefix='/history',tags=['History'])
@router.get('')
def list_history(page:int=1,page_size:int=20,date_start:datetime|None=None,date_end:datetime|None=None,user_email:str|None=None,field:str|None=None,eco:str|None=None,db:Session=Depends(get_db),user=Depends(current_user)):
    if user.role != 'admin':
        permission = db.scalar(select(AnalystPermission).where(AnalystPermission.user_email == user.email))
        if not permission or not permission.can_view_history:
            raise HTTPException(status_code=403, detail='Você não possui permissão para visualizar o histórico.')

    items,total=HistoryRepository(db).list(page,page_size,date_start,date_end,user_email,field,eco)
    if user.role != 'admin':
        hidden_fields = {
            ('group' if item.field_key == 'group_name' else item.field_key)
            for item in db.scalars(select(FieldPermission).where(FieldPermission.user_email == user.email)).all()
            if item.can_view is False
        }
        items = [item for item in items if item.field_key not in hidden_fields]

    data=[{c.name:getattr(x,c.name) for c in x.__table__.columns} for x in items]
    for x in data: x['id']=str(x['id']); x['eco_id']=str(x['eco_id']) if x['eco_id'] else None
    return {'items':data,'total':total,'page':page,'page_size':page_size}
