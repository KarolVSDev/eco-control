from fastapi import HTTPException
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models.entities import (
    User,
    AnalystPermission,
    FieldPermission,
)

from app.repository.user_repository import (
    UserRepository,
)

from app.schemas.user import (
    UserCreate,
)

from app.utils.security import (
    hash_password,
)


class UserService:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

        self.repository = (
            UserRepository(db)
        )


    # =========================================================
    # LISTAR
    # =========================================================

    def list_users(
        self,
    ):
        users = (
            self.repository
            .list_all()
        )

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


    # =========================================================
    # CRIAR
    # =========================================================

    def create_user(
        self,
        payload: UserCreate,
    ):
        email = (
            payload.email
            .lower()
            .strip()
        )


        existing_user = (
            self.repository
            .get_by_email(
                email
            )
        )


        if existing_user:

            raise HTTPException(
                status_code=409,
                detail=(
                    "Já existe um usuário "
                    "cadastrado com este e-mail."
                ),
            )


        user = User(
            email=email,
            full_name=(
                payload.full_name
                .strip()
            ),
            hashed_password=(
                hash_password(
                    payload.password
                )
            ),
            role=payload.role,
            active=payload.active,
        )


        self.repository.create(
            user
        )


        # -----------------------------------------------------
        # CONFIGURAÇÃO INICIAL DO ANALISTA
        # -----------------------------------------------------

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

        self.db.refresh(
            user
        )


        return {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "active": user.active,
        }


    # =========================================================
    # REDEFINIR SENHA PELO ADMIN
    # =========================================================

    def reset_password(
        self,
        user_id,
        new_password: str,
    ):
        user = (
            self.repository
            .get(
                user_id
            )
        )


        if not user:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Usuário não encontrado."
                ),
            )


        user.hashed_password = (
            hash_password(
                new_password
            )
        )


        self.db.commit()


        return {
            "message":
                "Senha redefinida com sucesso."
        }


    # =========================================================
    # EXCLUIR
    # =========================================================

    def delete_user(
        self,
        user_id,
        current_admin,
    ):
        user = (
            self.repository
            .get(
                user_id
            )
        )


        if not user:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Usuário não encontrado."
                ),
            )


        # -----------------------------------------------------
        # NÃO PERMITIR AUTOEXCLUSÃO
        # -----------------------------------------------------

        if (
            user.id
            == current_admin.id
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "Você não pode excluir "
                    "a própria conta."
                ),
            )


        # -----------------------------------------------------
        # REMOVER PERMISSÕES DO USUÁRIO
        # -----------------------------------------------------

        self.db.execute(
            delete(
                FieldPermission
            ).where(
                FieldPermission.user_email
                == user.email
            )
        )


        self.db.execute(
            delete(
                AnalystPermission
            ).where(
                AnalystPermission.user_email
                == user.email
            )
        )


        # -----------------------------------------------------
        # EXCLUIR USUÁRIO
        # -----------------------------------------------------

        self.repository.delete(
            user
        )


        self.db.commit()