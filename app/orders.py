from fastapi import APIRouter, Depends, HTTPException,Request
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Order, OrderItems, Product,Payment
import uuid

router = APIRouter()

@router.get("")#list all orders
def get_orders(request: Request,
    db: Session = Depends(get_db)
    
):
    current_user = request.state.user
    orders = (
        db.query(Order)
        .filter(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
        .all()
    )
    
    return [
        {
            "id": o.id,
            "amount": o.amount,
            "currency": o.currency,
            "status": o.status,
            "created_at": o.created_at
        }
        for o in orders
    ]



@router.get("/{order_id}")#get a single order
def get_order_details(request: Request,
    order_id: int,
    db: Session = Depends(get_db),
    
):
    current_user = request.state.user
    order = (
        db.query(Order)
        .filter(
            Order.id == order_id,
            Order.user_id == current_user.id
        )
        .first()
    )

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    items = (
        db.query(OrderItems, Product)
        .join(Product, Product.id == OrderItems.product_id)
        .filter(OrderItems.order_id == order.id)
        .all()
    )
    data = {
        "id": order.id,
        "amount": order.amount,
        "currency": order.currency,
        "status": order.status,
        "created_at": order.created_at,
        "items": [
            {
                "product_id": product.id,
                "title": product.title,
                "price": oi.price_at_purchase,
                "quantity": oi.quantity,
                "subtotal": oi.price_at_purchase * oi.quantity
            }
            for oi, product in items
        ]
    }
    if order.status == "PAID":
        payment = (
        db.query(Payment)
        .filter(Payment.order_id == order.id)
        .first())
        data["payment"]=payment.gateway_payment_id
    if order.status == "REFUNDED":
            payment = (
            db.query(Payment)
            .filter(
                Payment.order_id == order.id,
                Payment.status == "refund"
            )
            .order_by(Payment.created_at.desc())
            .first()
        )

            data["payment"] = payment.gateway_payment_id if payment else None


    return data

@router.post("/{order_id}/cancel")
def cancel_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != "PENDING":
        raise HTTPException(
            status_code=400,
            detail="Only pending orders can be cancelled"
        )

    order.status = "CANCELLED"
    db.commit()

    return {
        "message": "Order cancelled",
        "order_id": order.id,
        "status": order.status
    }
@router.post("/{order_id}/refund")
def refund_order(order_id: int, db: Session = Depends(get_db)):
    
    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != "PAID":
        raise HTTPException(
            status_code=400,
            detail="Only paid orders can be refunded"
        )
    items = db.query(OrderItems).filter(OrderItems.order_id == order.id).all()

    for item in items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        product.stock += item.quantity

    refund_payment = Payment(
        order_id=order.id,
        amount=-order.amount, 
        status="refund",
        gateway="mock",
        gateway_payment_id=f"REFUND-{uuid.uuid4().hex[:12]}"
    )

    db.add(refund_payment)
    order.status = "REFUNDED"
    db.commit()
    

    return {
        "message": "Order refunded",
        "order_id": order.id,
        "status": order.status
    }