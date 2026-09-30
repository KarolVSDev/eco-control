from fastapi import HTTPException
from sqlalchemy import select

from app.models.entities import User

from app.utils.security import (
    verify_password,
    hash_password,
    create_token,
)


class AuthService:

    def __init__(
        self,
        db,
    ):
        self.db = db


    # =========================================================
    # LOGIN
    # =========================================================

    def login(
        self,
        email,
        password,
    ):
        user = self.db.scalar(
            select(User).where(
                User.email == email
            )
        )


        if (
            not user
            or not verify_password(
                password,
                user.hashed_password,
            )
        ):

            raise HTTPException(
                status_code=401,
                detail=(
                    "E-mail ou senha inválidos"
                ),
            )


        return (
            user,
            create_token(user),
        )


    # =========================================================
    # ALTERAR A PRÓPRIA SENHA
    # =========================================================

    def change_password(
        self,
        user,
        current_password: str,
        new_password: str,
    ):
        if not verify_password(
            current_password,
            user.hashed_password,
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "A senha atual está incorreta."
                ),
            )


        if verify_password(
            new_password,
            user.hashed_password,
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "A nova senha deve ser "
                    "diferente da senha atual."
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
                "Senha alterada com sucesso."
        }