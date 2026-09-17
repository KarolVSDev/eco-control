from fastapi import APIRouter,Depends,Query,Response
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.schemas.eco import EcoCreate,EcoUpdate
from app.services.eco_service import EcoService
from app.utils.security import current_user
router=APIRouter(prefix='/ecos',tags=['ECOs'])
@router.get('')
def list_ecos(page:int=1,page_size:int=50,search:str|None=None,status:str|None=None,month:str|None=None,db:Session=Depends(get_db),user=Depends(current_user)):
    items,total=EcoService(db,user).list(page=page,page_size=page_size,search=search,status=status,month=month); return {'items':items,'total':total,'page':page,'page_size':page_size}
@router.post('')
def create(body:EcoCreate,db:Session=Depends(get_db),user=Depends(current_user)): return EcoService(db,user).create(body)
@router.patch('/{eco_id}')
def update(eco_id:str,body:EcoUpdate,db:Session=Depends(get_db),user=Depends(current_user)): return EcoService(db,user).update(eco_id,body)
@router.delete('/{eco_id}',status_code=204)
def delete(eco_id:str,db:Session=Depends(get_db),user=Depends(current_user)): EcoService(db,user).delete(eco_id); return Response(status_code=204)
