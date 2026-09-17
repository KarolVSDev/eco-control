from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import select, update
from app.models.entities import Eco, EcoHistory, AnalystPermission, FieldPermission
from app.repository.eco_repository import EcoRepository
from app.repository.history_repository import HistoryRepository
from app.repository.settings_repository import SettingsRepository
from app.utils.eco_calculations import compute_eco_fields, normalize_text

MONTHS=['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']
LABELS={'status':'status','group_name':'group','obu':'obu','au':'au','owner':'owner','eco':'ECO','comments':'comments'}

class EcoService:
    def __init__(self,db,user):
        self.db=db; self.user=user; self.repo=EcoRepository(db); self.history=HistoryRepository(db); self.settings=SettingsRepository(db)
    def _field_permissions(self):
        return {p.field_key:p for p in self.db.scalars(select(FieldPermission).where(FieldPermission.user_email==self.user.email)).all()}
    def _filter_allowed(self, changes):
        if self.user.role=='admin': return changes
        perms=self._field_permissions(); allowed={}
        for key,val in changes.items():
            external='group' if key=='group_name' else key
            p=perms.get(external)
            if p and p.can_edit: allowed[key]=val
        if not allowed: raise HTTPException(403,'Nenhum dos campos enviados pode ser editado por você.')
        return allowed
    def _can_create(self):
        if self.user.role=='admin': return True
        p=self.db.scalar(select(AnalystPermission).where(AnalystPermission.user_email==self.user.email))
        return bool(p and p.can_create_eco)
    def list(self,**kwargs):
        items,total=self.repo.list(**kwargs); return [self.serialize(x) for x in items],total
    def serialize(self, e):
        data = {
            column.name:
                getattr(e, column.name)
            for column
            in e.__table__.columns
        }

        data["id"] = str(e.id)

        data["group"] = data.pop(
            "group_name"
        )

        computed = compute_eco_fields(e)

        data.update(computed)

        data["computed"] = computed


        # Administrador visualiza tudo.
        if self.user.role == "admin":
            return data


        permissions = (
            self._field_permissions()
        )


    # Remove da resposta os campos
    # explicitamente bloqueados
    # para visualização.
        for (
            field_key,
            permission,
        ) in permissions.items():

            if (
                permission.can_view
                is False
            ):
                data.pop(
                    field_key,
                    None,
                )


            return data
    # def serialize(self,e):
    #     data={c.name:getattr(e,c.name) for c in e.__table__.columns}; data['id']=str(e.id); data['group']=data.pop('group_name'); data['computed']=compute_eco_fields(e); return data
    def create(self,payload):
        if not self._can_create(): raise HTTPException(403,'Você não possui permissão para criar novas ECOs.')
        d={k:normalize_text(v) for k,v in payload.model_dump(exclude_none=True).items()}; group=d.pop('group',None)
        d=self._filter_allowed({**d, **({'group_name':group} if group else {})}) if self.user.role!='admin' else {**d, **({'group_name':group} if group else {})}
        group=d.pop('group_name',None)
        if d.get('obu'): d['au']=self.settings.au_for_obu(d['obu'])
        if d.get('owner') and not group: group=self.settings.group_for_owner(d['owner'])
        n=self.repo.next_item(); e=Eco(**d,group_name=group,item=n,position=n,month=MONTHS[datetime.now().month-1])
        self.repo.create(e); self.history.add(EcoHistory(eco_id=e.id,eco_code=e.eco,item=e.item,field_key='eco',field_label='ECO criada',new_value=e.eco,user_email=self.user.email,user_name=self.user.full_name,action='created'))
        self.db.commit(); return self.serialize(e)
    def update(self,id,payload):
        e=self.repo.get(id)
        if not e: raise HTTPException(404,'ECO não encontrada')
        changes={k:normalize_text(v) for k,v in payload.model_dump(exclude_unset=True).items()}
        if 'group' in changes: changes['group_name']=changes.pop('group')
        changes=self._filter_allowed(changes)
        if changes.get('obu'): changes['au']=self.settings.au_for_obu(changes['obu'])
        if changes.get('owner') and 'group_name' not in changes:
            mapped=self.settings.group_for_owner(changes['owner'])
            if mapped: changes['group_name']=mapped
        for k,v in changes.items():
            old=getattr(e,k)
            if old!=v:
                setattr(e,k,v); self.history.add(EcoHistory(eco_id=e.id,eco_code=e.eco,item=e.item,field_key=k,field_label=LABELS.get(k,k),old_value=str(old or ''),new_value=str(v or ''),user_email=self.user.email,user_name=self.user.full_name,action='updated'))
        self.db.commit(); return self.serialize(e)
    def delete(self,id):
        if self.user.role!='admin': raise HTTPException(403,'Somente administradores podem excluir ECOs.')
        e=self.repo.get(id)
        if not e: raise HTTPException(404,'ECO não encontrada')
        deleted_item=e.item or 0
        self.history.add(EcoHistory(eco_id=e.id,eco_code=e.eco,item=e.item,field_key='eco',field_label='ECO excluída',old_value=e.eco,user_email=self.user.email,user_name=self.user.full_name,action='deleted'))
        self.repo.delete(e); self.db.flush()
        if deleted_item:
            self.db.execute(update(Eco).where(Eco.item>deleted_item).values(item=Eco.item-1))
        self.db.commit()
