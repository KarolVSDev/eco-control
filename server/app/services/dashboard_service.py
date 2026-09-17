from sqlalchemy import select, func
from app.models.entities import Eco
from app.utils.eco_calculations import compute_eco_fields
class DashboardService:
    def __init__(self,db): self.db=db
    def _rows(self,month=None):
        q=select(Eco)
        if month: q=q.where(Eco.month==month)
        return self.db.scalars(q).all()
    def months(self):
        order=['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']
        vals=set(self.db.scalars(select(Eco.month).where(Eco.month.is_not(None))).all()); return [m for m in order if m in vals]
    def stats(self):
        rows=self._rows(); comps=[compute_eco_fields(r) for r in rows]
        count=lambda s: sum(1 for r in rows if r.status==s)
        return {'total':len(rows),'working':count('WORKING'),'on_hold':count('ON HOLD'),'processing':count('PROCESSING'),'released':count('RELEASED'),'rejected':count('REJECTED'),'cancelled':sum(1 for r in rows if r.status in ('CANCELLED','TO BE CANCELLED')),'overdue':0,'gap7':sum(1 for c in comps if c['contar_eco_7']),'gap14':sum(1 for c in comps if c['contar_eco_14'])}
    def group(self,dimension,month=None):
        mapping={'status':Eco.status,'group':Eco.group_name,'owner':Eco.owner,'obu':Eco.obu,'au':Eco.au,'eco_type':Eco.eco_type}
        col=mapping[dimension]; q=select(col,func.count(Eco.id)).group_by(col)
        if month: q=q.where(Eco.month==month)
        data=[]
        for name,val in self.db.execute(q).all():
            key=(name or 'N/A').strip() if isinstance(name,str) else 'N/A'; data.append({'name':key,'value':val})
        merged={}
        for d in data: merged[d['name']]=merged.get(d['name'],0)+d['value']
        return [{'name':k,'value':v} for k,v in sorted(merged.items(),key=lambda x:x[1],reverse=True)]
    def evolution(self):
        order=['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']; g={d['name']:d['value'] for d in self.group_by_month()}; return [{'name':m,'value':g[m]} for m in order if m in g]
    def group_by_month(self):
        return [{'name':m or 'N/A','value':v} for m,v in self.db.execute(select(Eco.month,func.count(Eco.id)).group_by(Eco.month)).all()]
    def delay(self,month=None):
        cats={'No prazo':0,'1-7 dias':0,'8-14 dias':0,'> 14 dias':0}
        for r in self._rows(month):
            gap=compute_eco_fields(r)['az_gap']
            if gap is None or gap<=0: cats['No prazo']+=1
            elif gap<=7: cats['1-7 dias']+=1
            elif gap<=14: cats['8-14 dias']+=1
            else: cats['> 14 dias']+=1
        return [{'name':k,'value':v} for k,v in cats.items()]
    def monthly_summary(self):
        order=['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']; out=[]
        for m in order:
            rows=self._rows(m)
            if not rows: continue
            out.append({'month':m,'total':len(rows),'working':sum(r.status=='WORKING' for r in rows),'processing':sum(r.status=='PROCESSING' for r in rows),'cancelled':sum(r.status in ('CANCELLED','TO BE CANCELLED') for r in rows),'released':sum(r.status=='RELEASED' for r in rows),'rejected':sum(r.status=='REJECTED' for r in rows)})
        return out
