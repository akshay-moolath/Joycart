from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Product

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/products/{product_id}")
def product_page(
    request: Request,
    product_id: int,
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return templates.TemplateResponse(
        "product.html",
        {
            "request": request,
            "product": product
        }
    )
