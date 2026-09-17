from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.entities import User, AnalystPermission
from app.repository.user_repository import UserRepository
from app.schemas.user import UserCreate
from app.utils.security import hash_password


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = UserRepository(db)

    def list_users(self):
        users = self.repository.list_all()

        return [
            {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "active": user.active,
            }
            for user in users
        ]

    def create_user(self, payload: UserCreate):
        email = payload.email.lower().strip()

        existing_user = self.repository.get_by_email(email)

        if existing_user:
            raise HTTPException(
                status_code=409,
                detail="Já existe um usuário cadastrado com este e-mail.",
            )

        user = User(
            email=email,
            full_name=payload.full_name.strip(),
            hashed_password=hash_password(payload.password),
            role=payload.role,
            active=payload.active,
        )

        self.repository.create(user)

        # Cria configuração inicial para analistas.
        if payload.role == "analyst":
            self.db.add(
                AnalystPermission(
                    user_email=email,
                    can_create_eco=False,
                    can_bulk_edit=False,
                    can_view_history=True,
                )
            )

        self.db.commit()
        self.db.refresh(user)

        return {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "active": user.active,
        }