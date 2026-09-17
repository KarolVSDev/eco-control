from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import (
    AnalystPermission,
    FieldPermission,
)


class PermissionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_general(
        self,
        user_email: str,
    ):
        return self.db.scalar(
            select(AnalystPermission).where(
                AnalystPermission.user_email
                == user_email
            )
        )

    def get_fields(
        self,
        user_email: str,
    ):
        return self.db.scalars(
            select(FieldPermission)
            .where(
                FieldPermission.user_email
                == user_email
            )
            .order_by(
                FieldPermission.field_key
            )
        ).all()

    def create_general(
        self,
        permission: AnalystPermission,
    ):
        self.db.add(permission)
        self.db.flush()

        return permission

    def get_field(
        self,
        user_email: str,
        field_key: str,
    ):
        return self.db.scalar(
            select(FieldPermission).where(
                FieldPermission.user_email
                == user_email,
                FieldPermission.field_key
                == field_key,
            )
        )

    def create_field(
        self,
        permission: FieldPermission,
    ):
        self.db.add(permission)
        self.db.flush()

        return permission