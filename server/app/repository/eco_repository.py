from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session
from app.models.entities import Eco
class EcoRepository:
    def __init__(self, db:Session): self.db=db
    def list(self,page=1,page_size=50,search=None,status=None,month=None):
        q=select(Eco); count=select(func.count()).select_from(Eco)
        filters=[]
        if search: filters.append(or_(Eco.eco.ilike(f'%{search}%'), Eco.owner.ilike(f'%{search}%')))
        if status: filters.append(Eco.status==status)
        if month: filters.append(Eco.month==month)
        if filters: q=q.where(*filters); count=count.where(*filters)
        total=self.db.scalar(count) or 0
        items=self.db.scalars(q.order_by(Eco.item.desc()).offset((page-1)*page_size).limit(page_size)).all()
        return items,total
    def get(self,id): return self.db.get(Eco,id)
    def next_item(self): return (self.db.scalar(select(func.max(Eco.item))) or 0)+1
    def create(self,eco): self.db.add(eco); self.db.flush(); return eco
    def delete(self,eco): self.db.delete(eco)
