from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Response,
    status,
)

from sqlalchemy.orm import Session

from app.config.database import get_db

from app.schemas.settings import (
    ManagerPayload,
    ObuAuPayload,
    OwnerGroupPayload,
)

from app.services.settings_service import (
    SettingsService,
)

from app.utils.security import (
    admin_user,
)


router = APIRouter(
    prefix="/settings",
    tags=["Settings"],
)


# =========================================================
# OBU → AU
# =========================================================

@router.post(
    "/obu-au",
    status_code=status.HTTP_201_CREATED,
)
def create_obu_au(
    body: ObuAuPayload,
    db: Session = Depends(get_db),
    _=Depends(admin_user),
):
    return SettingsService(
        db
    ).create_obu_au(
        body
    )


@router.put(
    "/obu-au/{mapping_id}",
)
def update_obu_au(
    mapping_id: UUID,
    body: ObuAuPayload,
    db: Session = Depends(get_db),
    _=Depends(admin_user),
):
    return SettingsService(
        db
    ).update_obu_au(
        mapping_id,
        body,
    )


@router.delete(
    "/obu-au/{mapping_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_obu_au(
    mapping_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(admin_user),
):
    SettingsService(
        db
    ).delete_obu_au(
        mapping_id
    )

    return Response(
        status_code=(
            status.HTTP_204_NO_CONTENT
        )
    )


# =========================================================
# OWNER → GROUP
# =========================================================

@router.post(
    "/owner-group",
    status_code=status.HTTP_201_CREATED,
)
def create_owner_group(
    body: OwnerGroupPayload,
    db: Session = Depends(get_db),
    _=Depends(admin_user),
):
    return SettingsService(
        db
    ).create_owner_group(
        body
    )


@router.delete(
    "/owner-group/{mapping_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_owner_group(
    mapping_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(admin_user),
):
    SettingsService(
        db
    ).delete_owner_group(
        mapping_id
    )

    return Response(
        status_code=(
            status.HTTP_204_NO_CONTENT
        )
    )


# =========================================================
# GERENTES
# =========================================================

@router.post(
    "/managers",
    status_code=status.HTTP_201_CREATED,
)
def create_manager(
    body: ManagerPayload,
    db: Session = Depends(get_db),
    _=Depends(admin_user),
):
    return SettingsService(
        db
    ).create_manager(
        body
    )


@router.delete(
    "/managers/{manager_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_manager(
    manager_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(admin_user),
):
    SettingsService(
        db
    ).delete_manager(
        manager_id
    )

    return Response(
        status_code=(
            status.HTTP_204_NO_CONTENT
        )
    )