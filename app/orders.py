from fastapi import APIRouter, Depends, HTTPException,Request
from sqlalchemy.orm import Session
from app.db import get_db
from fastapi.templating import Jinja2Templates
from app.auth import get_current_user
from app.models import Order, OrderItems, Product,Payment,Cart
import uuid
from datetime import datetime, timedelta

router = APIRouter()
pages_router = APIRouter()

templates = Jinja2Templates(directory="templates")

######################PLACE ORDER###########################

@router.post("/place")
def place_order(request: Request,
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

    
    #db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()

    db.commit()

    return {"order_id": order.id}

############################GET ORDERS##############################

@router.get("/{order_id}")
def get_single_order(request: Request,
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

@pages_router.get("/orders")
def get_all_orders(request: Request, db: Session = Depends(get_db)):

    current_user = request.state.user 
    
    orders = db.query(Order).filter(Order.user_id ==current_user.id).order_by(Order.created_at.desc()).all()

    return templates.TemplateResponse(
        "orders.html",
        {
            "request": request, 
            "orders": orders
            
        }
    )

#######################################CANCEL AND REFUND ORDERS###################################

@router.post("/cancel/{order_id}")
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
@router.post("/refund/{order_id}")
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



@pages_router.get("/orders/{order_id}")
def order_detail_page(request: Request):
    return templates.TemplateResponse(
        "orderdetails.html",
        {"request": request}
    )
@pages_router.get("/orders/summary")
def order_summary(request: Request):
    return templates.TemplateResponse(
        "order_summary.html",
        {"request": request}
    )