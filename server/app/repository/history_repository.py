from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.entities import EcoHistory
class HistoryRepository:
    def __init__(self,db): self.db=db
    def add(self,h): self.db.add(h)
    def list(self,page=1,page_size=20,date_start=None,date_end=None,user_email=None,field=None,eco=None):
        q=select(EcoHistory); c=select(func.count()).select_from(EcoHistory); fs=[]
        if date_start: fs.append(EcoHistory.created_at>=date_start)
        if date_end: fs.append(EcoHistory.created_at<=date_end)
        if user_email: fs.append(EcoHistory.user_email==user_email)
        if field: fs.append(EcoHistory.field_label==field)
        if eco: fs.append(EcoHistory.eco_code.ilike(f'%{eco}%'))
        if fs: q=q.where(*fs); c=c.where(*fs)
        total=self.db.scalar(c) or 0
        items=self.db.scalars(q.order_by(EcoHistory.created_at.desc()).offset((page-1)*page_size).limit(page_size)).all()
        return items,total
