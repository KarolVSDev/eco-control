from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.entities import (
    AnalystPermission,
    FieldPermission,
)
from app.schemas.auth import LoginRequest
from app.services.auth_service import AuthService
from app.utils.security import current_user


router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


@router.post("/login")
def login(
    body: LoginRequest,
    db: Session = Depends(get_db),
):
    user, token = AuthService(db).login(
        body.email,
        body.password,
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
        },
    }


@router.get("/permissions")
def my_permissions(
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    # Administrador sempre possui acesso total.
    if user.role == "admin":
        return {
            "role": "admin",
            "general": {
                "can_create_eco": True,
                "can_bulk_edit": True,
                "can_view_history": True,
            },
            "fields": [],
        }

    general = db.scalar(
        select(
            AnalystPermission
        ).where(
            AnalystPermission.user_email
            == user.email
        )
    )

    fields = db.scalars(
        select(
            FieldPermission
        ).where(
            FieldPermission.user_email
            == user.email
        )
    ).all()

    return {
        "role": user.role,

        "general": {
            "can_create_eco": (
                general.can_create_eco
                if general
                else False
            ),

            "can_bulk_edit": (
                general.can_bulk_edit
                if general
                else False
            ),

            "can_view_history": (
                general.can_view_history
                if general
                else True
            ),
        },

        "fields": [
            {
                "field_key":
                    permission.field_key,

                "can_view":
                    permission.can_view,

                "can_edit":
                    permission.can_edit,
            }
            for permission in fields
        ],
    }