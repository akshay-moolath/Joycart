from datetime import datetime, timedelta
from typing import Optional
from jose import jwt,JWTError
import os
from fastapi import Depends, HTTPException, status,Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.db import get_db
from app import models
from dotenv import load_dotenv


load_dotenv()
JWT_SECRET=os.getenv("JWT_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
bearer = HTTPBearer()

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)
    return token

def decode_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
):
    token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    data = decode_token(token)
    username = data.get("sub")

    if not username:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = (
        db.query(models.User)
        .filter(models.User.username == username)
        .first()
    )

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user
