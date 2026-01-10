from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from app.db.db import get_db
from app.db.models import Product
from app.auth import get_current_user_optional

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/products/{product_id}")
def product_page(
    request: Request,
    product_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return templates.TemplateResponse(
        "product.html",
        {
            "request": request,
            "product": product,
            "current_user": current_user
        }
    )

def list_products(db: Session = Depends(get_db)):
    return db.query(Product).order_by(Product.id.asc()).all()
    




