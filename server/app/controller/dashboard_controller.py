from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.services.dashboard_service import DashboardService
from app.utils.security import current_user
router=APIRouter(prefix='/dashboard',tags=['Dashboard'])
@router.get('/stats')
def stats(db:Session=Depends(get_db),_=Depends(current_user)): return DashboardService(db).stats()
@router.get('/months')
def months(db:Session=Depends(get_db),_=Depends(current_user)): return DashboardService(db).months()
@router.get('/group/{dimension}')
def group(dimension:str,month:str|None=None,db:Session=Depends(get_db),_=Depends(current_user)):
    if dimension not in {'status','group','owner','obu','au','eco_type'}: raise HTTPException(400,'Dimensão inválida')
    return DashboardService(db).group(dimension,month)
@router.get('/evolution')
def evolution(db:Session=Depends(get_db),_=Depends(current_user)): return DashboardService(db).evolution()
@router.get('/delay')
def delay(month:str|None=None,db:Session=Depends(get_db),_=Depends(current_user)): return DashboardService(db).delay(month)
@router.get('/monthly-summary')
def monthly(db:Session=Depends(get_db),_=Depends(current_user)): return DashboardService(db).monthly_summary()
