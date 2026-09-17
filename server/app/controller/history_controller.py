from datetime import datetime
from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.repository.history_repository import HistoryRepository
from app.utils.security import current_user
router=APIRouter(prefix='/history',tags=['History'])
@router.get('')
def list_history(page:int=1,page_size:int=20,date_start:datetime|None=None,date_end:datetime|None=None,user_email:str|None=None,field:str|None=None,eco:str|None=None,db:Session=Depends(get_db),_=Depends(current_user)):
    items,total=HistoryRepository(db).list(page,page_size,date_start,date_end,user_email,field,eco)
    data=[{c.name:getattr(x,c.name) for c in x.__table__.columns} for x in items]
    for x in data: x['id']=str(x['id']); x['eco_id']=str(x['eco_id']) if x['eco_id'] else None
    return {'items':data,'total':total,'page':page,'page_size':page_size}
