# app/crud/user.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.db import get_db
from app.auth import hash_password, verify_password, create_access_token
from app.models import User
from app.schemas import UserCreate, UserOut, LoginSchema

router = APIRouter()

@router.post("/users", response_model=UserOut)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="username already exists")
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="email already exists")

    user = User(
        username=payload.username,
        email=payload.email,
        password=hash_password(payload.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user



@router.post("/login")  #stores token in the backend instead of sending to front end
def login_user(payload: LoginSchema, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        User.username == payload.username
    ).first()

    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(status_code=400, detail="Invalid username or password")

    token = create_access_token({"sub": user.username})

    response = JSONResponse({
        "message": "Login successful",
        "username": user.username,
        "email": user.email
    })

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,      # 🔐 JS cannot read it
        samesite="lax",     # 🛡️ CSRF protection
        secure=False        # True when HTTPS
    )

    return response