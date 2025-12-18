from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Cart, Product

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/cart")
def cart_page(
    request: Request,
    db: Session = Depends(get_db)
):


    cart = None
    items = []
    total = 0

    return templates.TemplateResponse(
        "viewcart.html",
        {
            "request": request,
            "cart": {
                "items": items,
                "total": total
            }
        }
    )
