from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Cart, Product
router = APIRouter()

@router.get("/view")
def get_cart(request: Request,
    db: Session = Depends(get_db),
    
):
    current_user = request.state.user
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