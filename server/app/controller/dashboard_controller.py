from fastapi import APIRouter,Depends,HTTPException,Query
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.services.dashboard_service import DashboardService
from app.utils.security import current_user
router=APIRouter(prefix='/dashboard',tags=['Dashboard'])
@router.get('/stats')
def stats(year:int|None=Query(default=None,ge=1,le=9998),db:Session=Depends(get_db),_=Depends(current_user)): return DashboardService(db).stats(year)
@router.get('/months')
def months(year:int|None=Query(default=None,ge=1,le=9998),db:Session=Depends(get_db),_=Depends(current_user)): return DashboardService(db).months(year)
@router.get('/years')
def years(db:Session=Depends(get_db),_=Depends(current_user)): return DashboardService(db).years()
@router.get('/group/{dimension}')
def group(dimension:str,month:str|None=None,year:int|None=Query(default=None,ge=1,le=9998),db:Session=Depends(get_db),_=Depends(current_user)):
    if dimension not in {'status','group','owner','obu','au','eco_type'}: raise HTTPException(400,'Dimensão inválida')
    return DashboardService(db).group(dimension,month,year)
@router.get('/evolution')
def evolution(year:int|None=Query(default=None,ge=1,le=9998),db:Session=Depends(get_db),_=Depends(current_user)): return DashboardService(db).evolution(year)
@router.get('/delay')
def delay(month:str|None=None,year:int|None=Query(default=None,ge=1,le=9998),db:Session=Depends(get_db),_=Depends(current_user)): return DashboardService(db).delay(month,year)
@router.get('/monthly-summary')
def monthly(year:int|None=Query(default=None,ge=1,le=9998),db:Session=Depends(get_db),_=Depends(current_user)): return DashboardService(db).monthly_summary(year)
