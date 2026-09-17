from fastapi import HTTPException
from sqlalchemy import select
from app.models.entities import User
from app.utils.security import verify_password, create_token
class AuthService:
    def __init__(self,db): self.db=db
    def login(self,email,password):
        u=self.db.scalar(select(User).where(User.email==email))
        if not u or not verify_password(password,u.hashed_password): raise HTTPException(401,'E-mail ou senha inválidos')
        return u,create_token(u)
