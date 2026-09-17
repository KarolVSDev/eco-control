from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_all(self):
        return self.db.scalars(
            select(User).order_by(User.full_name)
        ).all()

    def get_by_email(self, email: str):
        return self.db.scalar(
            select(User).where(User.email == email)
        )

    def create(self, user: User):
        self.db.add(user)
        self.db.flush()

        return user