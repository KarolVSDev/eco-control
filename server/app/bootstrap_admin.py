import logging

from app.config.database import SessionLocal
from app.config.settings import settings
from app.repository.user_repository import UserRepository
from app.schemas.user import UserCreate
from app.services.user_service import UserService


logger = logging.getLogger(__name__)


def bootstrap_initial_admin() -> None:
    email = settings.admin_email.strip().lower()
    password = settings.admin_password
    name = settings.admin_name.strip() or "Administrador"

    if not email or not password:
        logger.info(
            "Initial administrator bootstrap skipped: "
            "ADMIN_EMAIL or ADMIN_PASSWORD is not configured"
        )
        return

    db = SessionLocal()
    try:
        repository = UserRepository(db)
        if repository.get_by_email(email):
            logger.info(
                "Initial administrator already exists: %s",
                email,
            )
            return

        UserService(db).create_user(
            UserCreate(
                email=email,
                full_name=name,
                password=password,
                role="admin",
                active=True,
            ),
        )

        logger.info(
            "Initial administrator created: %s",
            email,
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main() -> None:
    bootstrap_initial_admin()


if __name__ == "__main__":
    main()