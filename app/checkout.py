from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.db import get_db
from app.models import Cart, CartItem, Product, Order, OrderItems

router = APIRouter()


@router.post("/checkout")
def checkout(request: Request,
    db: Session = Depends(get_db)
    ):
    current_user = request.state.user
    cart = (
        db.query(Cart)
        .filter(Cart.user_id == current_user.id)
        .first()
    )

    if not cart or not cart.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    total_amount = 0
    order_items: list[OrderItems] = []

    for item in cart.items:
        product = (
            db.query(Product)
            .filter(Product.id == item.product_id)
            .first()
        )

        if not product:
            continue

        subtotal = product.price * item.quantity
        total_amount += subtotal

        order_items.append(
            OrderItems(
                product_id=product.id,
                quantity=item.quantity,
                seller_id=product.seller_id,
                price_at_purchase=product.price
            )
        )

    if total_amount == 0:
        raise HTTPException(status_code=400, detail="Invalid cart")

    
    order = Order(
        user_id=current_user.id,
        amount=total_amount,
        status="PENDING",
        currency="INR",
        expires_at=datetime.utcnow() + timedelta(minutes=30)
    )

    db.add(order)
    db.flush()  

    
    for oi in order_items:
        oi.order_id = order.id
        db.add(oi)

    
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()

    db.commit()

    return {
        "message": "Order created",
        "order_id": order.id,
        "amount": total_amount,
        "currency": "INR"
    }
