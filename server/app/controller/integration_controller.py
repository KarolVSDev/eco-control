from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.schemas.eco_automation import EcoAutomationRequest, EcoAutomationResponse
from app.services.eco_service import EcoService
from app.utils.security import current_user


router = APIRouter(prefix="/integrations", tags=["Integrations"])


@router.post("/eco-automation", response_model=EcoAutomationResponse)
def sync_eco_automation(
    body: EcoAutomationRequest,
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    return EcoService(db, user).sync_automation(body)
