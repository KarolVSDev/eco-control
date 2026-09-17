from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.entities import AnalystPermission, FieldPermission
from app.repository.settings_repository import SettingsRepository
from app.schemas.user import UserCreate
from app.services.user_service import UserService
from app.utils.security import admin_user
from app.schemas.permission import PermissionUpdate
from app.services.permission_service import PermissionService


router = APIRouter(tags=["Admin"])


@router.get("/users")
def users(
    db: Session = Depends(get_db),
    _=Depends(admin_user),
):
    return UserService(db).list_users()


@router.post(
    "/users",
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    body: UserCreate,
    db: Session = Depends(get_db),
    _=Depends(admin_user),
):
    return UserService(db).create_user(body)


@router.get("/settings")
def settings(
    db: Session = Depends(get_db),
    _=Depends(admin_user),
):
    repository = SettingsRepository(db)

    return {
        "obu_au": [
            {
                "id": str(item.id),
                "obu": item.obu,
                "au": item.au,
            }
            for item in repository.all_obu_au()
        ],
        "owner_group": [
            {
                "id": str(item.id),
                "owner": item.owner,
                "group": item.group_name,
            }
            for item in repository.all_owner_group()
        ],
        "managers": [
            {
                "id": str(item.id),
                "name": item.name,
            }
            for item in repository.all_managers()
        ],
    }


@router.get("/permissions")
def permissions(
    db: Session = Depends(get_db),
    _=Depends(admin_user),
):
    analyst_permissions = [
        {
            "user_email": permission.user_email,
            "can_create_eco": permission.can_create_eco,
            "can_bulk_edit": permission.can_bulk_edit,
            "can_view_history": permission.can_view_history,
        }
        for permission in db.scalars(
            select(AnalystPermission)
        ).all()
    ]

    field_permissions = [
        {
            "user_email": permission.user_email,
            "field_key": permission.field_key,
            "can_view": permission.can_view,
            "can_edit": permission.can_edit,
        }
        for permission in db.scalars(
            select(FieldPermission)
        ).all()
    ]

    return {
        "analyst": analyst_permissions,
        "fields": field_permissions,
    }

@router.get("/permissions/{user_email}")
def get_user_permissions(
    user_email: str,
    db: Session = Depends(get_db),
    _=Depends(admin_user),
):
    return PermissionService(
        db
    ).get_user_permissions(
        user_email
    )


@router.put("/permissions/{user_email}")
def update_user_permissions(
    user_email: str,
    body: PermissionUpdate,
    db: Session = Depends(get_db),
    _=Depends(admin_user),
):
    return PermissionService(
        db
    ).update_user_permissions(
        user_email,
        body,
    )