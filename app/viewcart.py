from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.auth import get_current_user
from app.db import get_db
from app.models import Cart, Product,User

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/view")
def get_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()

    if not cart:
        return {"items": [], "total": 0}

    items = []
    total = 0

    for item in cart.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            continue

        subtotal = product.price * item.quantity
        total += subtotal

        items.append({
            "id": item.id,
            "product_id": product.id,
            "title": product.title,
            "price": product.price,
            "quantity": item.quantity,
            "subtotal": subtotal,
            "thumbnail": product.thumbnail
        })

    return {
        "items": items,
        "total": total
    }