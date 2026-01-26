from datetime import datetime, timedelta
from typing import Optional
from jose import jwt,JWTError
import os
from fastapi import Depends, HTTPException, status,Request
from fastapi.security import HTTPBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.db.db import get_db
from app.db.models import User, Seller


JWT_SECRET=os.getenv("JWT_SECRET")
ALGORITHM = os.getenv("ALGORITHM")
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
    user_id= data.get("sub")

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = (
        db.query(User)
        .filter(User.id == int(user_id))
        .first()
    )

    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    if user.is_blocked:
        raise HTTPException(
            status_code=403,
            detail="Your account has been blocked"
        )

    request.state.user = user
    
    return user


def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    try:
        return get_current_user(request=request, db=db)
    except:
        return None

def get_current_seller(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):


    if not current_user or not current_user.is_seller:
        raise HTTPException(status_code=403, detail="Not a seller")

    seller = db.query(Seller).filter(
        Seller.user_id == current_user.id
    ).first()

    if not seller:
        raise HTTPException(status_code=403, detail="Seller not found")

    return seller

def get_current_admin(
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access only"
        )

    if current_user.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account is blocked"
        )

    return current_user