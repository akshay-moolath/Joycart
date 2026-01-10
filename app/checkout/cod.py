from fastapi import APIRouter,Request,Form ,Depends
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from app.db.db import get_db
from app.checkout.helper import helper
from app.db.models import User
from app.auth import get_current_user


templates = Jinja2Templates(directory="templates")

router = APIRouter()
pages_router = APIRouter()

@pages_router.get("/checkout/cod/confirm")
def cod_confirm_page(
    request: Request,
    checkout_id: str,
    current_user: User = Depends(get_current_user)    
):
    return templates.TemplateResponse(
        "cod_confirm.html",
        {
            "request": request,
            "checkout_id": checkout_id,
            "current_user":get_current_user
        }
    )

@router.post("/checkout/cod/confirm")
def place_cod_order(
    request: Request,
    checkout_id: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    method = "COD"

    helper(current_user,db,checkout_id,method,None)

    return RedirectResponse(
        "/checkout/cod/success",
        status_code=302
    )

@pages_router.get("/checkout/cod/success")
def cod_order_success(request:Request,
    current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse(
        "cod_success.html",
        {"request":request,
         "current_user":current_user}
    )