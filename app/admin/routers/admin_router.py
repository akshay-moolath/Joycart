from fastapi import APIRouter,  HTTPException, Depends, Request
import os
from sqlalchemy.orm import Session
from app.db.db import get_db
from app.db.models import User
from app.auth import get_current_admin
from fastapi.templating import Jinja2Templates
from app.admin.services.admin_service import get_users,block_users,unblock_users,make_admin



router = APIRouter(prefix="/admin")

templates = Jinja2Templates(directory="templates")

ADMIN_KEY = os.getenv("ADMIN_KEY")



@router.get("/users")
def list_users(
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
   return get_users(db)


@router.put("/users/{user_id}/block")
def block_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    return block_users(user_id,db,admin)


@router.put("/users/{user_id}/unblock")
def unblock_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    return unblock_users(user_id,db,admin)

@router.put("/users/{user_id}/make-admin")
def make_user_admin(
    user_id: int,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    return make_admin(user_id,db,admin)
    
@router.get("/dashboard")
def admin_dashboard(request:Request,
        current_admin = Depends(get_current_admin)):
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "current_user": current_admin
        }
    )
