from datetime import datetime, timedelta, timezone
import uuid
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.config.settings import settings
from app.models.entities import User
pwd = CryptContext(schemes=['bcrypt'], deprecated='auto')
bearer = HTTPBearer()
def hash_password(v): return pwd.hash(v)
def verify_password(v,h): return pwd.verify(v,h)
def create_token(user):
    exp=datetime.now(timezone.utc)+timedelta(minutes=settings.access_token_minutes)
    return jwt.encode({'sub':str(user.id),'email':user.email,'role':user.role,'exp':exp}, settings.jwt_secret, algorithm='HS256')
def current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer), db:Session=Depends(get_db)):
    token = credentials.credentials
    try: payload=jwt.decode(token,settings.jwt_secret,algorithms=['HS256']); uid=payload.get('sub')
    except JWTError: raise HTTPException(status_code=401, detail='Token inválido')
    user=db.get(User,uuid.UUID(uid))
    if not user or not user.active: raise HTTPException(status_code=401, detail='Usuário inválido')
    return user
def admin_user(user=Depends(current_user)):
    if user.role!='admin': raise HTTPException(status_code=403, detail='Acesso restrito a administrador')
    return user
