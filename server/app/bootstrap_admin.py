import os

from sqlalchemy import select

from app.config.database import SessionLocal
from app.models.entities import User
from app.utils.security import hash_password


ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
ADMIN_NAME = os.getenv(
    "ADMIN_NAME",
    "Administrador ECO CONTROL",
)


def main():
    if not ADMIN_EMAIL or not ADMIN_PASSWORD:
        raise RuntimeError(
            "ADMIN_EMAIL e ADMIN_PASSWORD precisam ser informados."
        )

    db = SessionLocal()

    try:
        existing_user = db.scalar(
            select(User).where(
                User.email == ADMIN_EMAIL
            )
        )

        if existing_user:
            print(
                f"O usuário {ADMIN_EMAIL} já existe. "
                "Nenhuma alteração foi realizada."
            )
            return

        admin = User(
            email=ADMIN_EMAIL,
            full_name=ADMIN_NAME,
            hashed_password=hash_password(
                ADMIN_PASSWORD
            ),
            role="admin",
            active=True,
        )

        db.add(admin)
        db.commit()

        print(
            "Administrador inicial criado com sucesso: "
            f"{ADMIN_EMAIL}"
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()