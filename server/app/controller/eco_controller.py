from fastapi import (
    APIRouter,
    Depends,
    Query,
    Response,
    status,
)
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.schemas.eco import (
    EcoCreate,
    EcoUpdate,
)
from app.services.eco_service import EcoService
from app.utils.security import current_user


router = APIRouter(
    prefix="/ecos",
    tags=["ECOs"],
)


# =========================================================
# LISTAR ECOS
# =========================================================

@router.get("")
def list_ecos(
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=50,
        ge=1,
        le=500,
    ),
    search: str | None = None,
    status_filter: str | None = Query(
        default=None,
        alias="status",
    ),
    month: str | None = None,
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    service = EcoService(
        db,
        user,
    )

    items, total = service.list(
        page=page,
        page_size=page_size,
        search=search,
        status=status_filter,
        month=month,
    )

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


# =========================================================
# CRIAR ECO
# =========================================================

@router.post("")
def create_eco(
    body: EcoCreate,
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    service = EcoService(
        db,
        user,
    )

    return service.create(
        body
    )


# =========================================================
# ATUALIZAR ECO
# =========================================================

@router.patch("/{eco_id}")
def update_eco(
    eco_id: str,
    body: EcoUpdate,
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    service = EcoService(
        db,
        user,
    )

    return service.update(
        eco_id,
        body,
    )


# =========================================================
# EXCLUIR ECO
# =========================================================

@router.delete(
    "/{eco_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_eco(
    eco_id: str,
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    service = EcoService(
        db,
        user,
    )

    service.delete(
        eco_id
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )