from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import (
    User,
    AnalystPermission,
    FieldPermission,
)
from app.repository.permission_repository import PermissionRepository
from app.schemas.permission import PermissionUpdate


class PermissionService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = PermissionRepository(db)

    def _get_analyst(self, email: str):
        user = self.db.scalar(
            select(User).where(
                User.email == email
            )
        )

        if not user:
            raise HTTPException(
                status_code=404,
                detail="Usuário não encontrado.",
            )

        if user.role != "analyst":
            raise HTTPException(
                status_code=400,
                detail=(
                    "Permissões específicas são "
                    "configuradas somente para analistas."
                ),
            )

        return user

    def get_user_permissions(
        self,
        email: str,
    ):
        user = self._get_analyst(email)

        general = self.repository.get_general(
            user.email
        )

        fields = self.repository.get_fields(
            user.email
        )

        return {
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
            },
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
                    "field_key": item.field_key,
                    "can_view": item.can_view,
                    "can_edit": item.can_edit,
                }
                for item in fields
            ],
        }

    def update_user_permissions(
        self,
        email: str,
        payload: PermissionUpdate,
    ):
        user = self._get_analyst(email)

        general = self.repository.get_general(
            user.email
        )

        if not general:
            general = AnalystPermission(
                user_email=user.email,
                can_create_eco=False,
                can_bulk_edit=False,
                can_view_history=True,
            )

            self.repository.create_general(
                general
            )

        general.can_create_eco = (
            payload.general.can_create_eco
        )

        general.can_bulk_edit = (
            payload.general.can_bulk_edit
        )

        general.can_view_history = (
            payload.general.can_view_history
        )

        for item in payload.fields:
            permission = self.repository.get_field(
                user.email,
                item.field_key,
            )

            if not permission:
                permission = FieldPermission(
                    user_email=user.email,
                    field_key=item.field_key,
                    can_view=item.can_view,
                    can_edit=item.can_edit,
                )

                self.repository.create_field(
                    permission
                )

            else:
                permission.can_view = item.can_view
                permission.can_edit = item.can_edit

        self.db.commit()

        return self.get_user_permissions(
            user.email
        )