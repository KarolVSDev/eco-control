from sqlalchemy import select
from app.models.entities import ObuAuMapping, OwnerGroupMapping, Manager
class SettingsRepository:
    def __init__(self,db): self.db=db
    def au_for_obu(self,obu):
        x=self.db.scalar(select(ObuAuMapping).where(ObuAuMapping.obu==obu)); return x.au if x else None
    def group_for_owner(self,owner):
        x=self.db.scalar(select(OwnerGroupMapping).where(OwnerGroupMapping.owner==owner)); return x.group_name if x else None
    def all_obu_au(self): return self.db.scalars(select(ObuAuMapping).order_by(ObuAuMapping.obu)).all()
    def all_owner_group(self): return self.db.scalars(select(OwnerGroupMapping).order_by(OwnerGroupMapping.owner)).all()
    def all_managers(self): return self.db.scalars(select(Manager).order_by(Manager.name)).all()
