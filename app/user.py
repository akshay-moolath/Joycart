# app/crud/user.py
from fastapi import APIRouter, Depends, HTTPException,Form
from fastapi.responses import JSONResponse,RedirectResponse
from sqlalchemy.orm import Session
from app.db import get_db
from app.auth import hash_password, verify_password, create_access_token
from app.models import User
from app.schemas import UserCreate, UserOut

router = APIRouter()

@router.post("/register") #for html redirect
def create_user(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    if db.query(User).filter(User.username == username).first():
        return RedirectResponse("/register?error=username", status_code=302)

    if db.query(User).filter(User.email == email).first():
        return RedirectResponse("/register?error=email", status_code=302)

    user = User(
        username=username,
        email=email,
        password=hash_password(password)
    )

    db.add(user)
    db.commit()

    return RedirectResponse("/login", status_code=302)

@router.post("/registerjs", response_model=UserOut) # for front end when using js,route url can be same ,because only first one works,but for safety name differently
def create_user(username: str = Form(...),email:str = Form(...),
    password: str = Form(...), db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="username already exists")
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="email already exists")

    user = User(
        username=username,
        email=email,
        password=hash_password(password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login")
def login_user( username: str = Form(...),
    password: str = Form(...), 
    db: Session = Depends(get_db)):

    user = db.query(User).filter(
        User.username == username
    ).first()

    if not user or not verify_password(password, user.password):
        return RedirectResponse(
            "/login?error=1",
            status_code=302
        )

    token = create_access_token({"sub": user.username})

    response = RedirectResponse(
        "/dashboard",
        status_code=302
    )

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/"  
    )

    return response

@router.post("/logout")
def logout():
    response = RedirectResponse("/", status_code=302)
    response.delete_cookie("access_token")
    return response