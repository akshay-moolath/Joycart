from fastapi import APIRouter, Depends, HTTPException,Request
from sqlalchemy.orm import Session
from app.db.db import get_db
from fastapi.templating import Jinja2Templates
from app.db.models import Order, OrderItems, Product,Payment, User
from app.auth import get_current_user


router = APIRouter()
pages_router = APIRouter()

templates = Jinja2Templates(directory="templates")


@router.get("/{order_id}")
def get_single_order(request: Request,
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    
):
    
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
            {   "item_id":oi.id,
                "product_id": product.id,
                "title": product.title,
                "price": oi.price_at_purchase,
                "quantity": oi.quantity,
                "status": oi.status,
                "subtotal": f"{(oi.price_at_purchase * oi.quantity):.2f}",
                "thumbnail":product.thumbnail
            }
            for oi, product in items
        ],
        "payment": None
    }

    payment = (
        db.query(Payment)
        .filter(Payment.order_id == order.id)
        .order_by(Payment.created_at.desc())
        .first()
    )

    if payment:
        data["payment"] = {
            "method": payment.method,
            "status": payment.status,
            "gateway_id": payment.gateway_payment_id
        }

    return data

@pages_router.get("/orders")
def get_all_orders(request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)):

    
    orders = db.query(Order).filter(Order.user_id ==current_user.id).order_by(Order.created_at.desc()).all()

    return templates.TemplateResponse(
        "orders.html",
        {
            "request": request, 
            "orders": orders
            
        }
    )

@pages_router.get("/orders/{order_id}")
def order_detail_page(request: Request):
    return templates.TemplateResponse(
        "orderdetails.html",
        {"request": request}
    )


#######################################CANCEL AND REFUND ORDERS###################################

@router.post("/{order_id}/cancel")
def cancel_entire_order(request:Request,
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    
    

    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user.id
    ).first()

    if not order:
        raise HTTPException(404)

    items = db.query(OrderItems).filter(
        OrderItems.order_id == order.id
    ).all()

    for item in items:
        if item.status in ["SHIPPED", "DELIVERED"]:
            raise HTTPException(
                400,
                "Cannot cancel order after shipping one item"
            )

    for item in items:
        if item.status in ["PLACED", "ACCEPTED"]:
            restore_stock_for_item(item, db)
            refund_order_item(item, db)  
            item.status = "CANCELLED"
    db.commit()

    return {"message": "Order cancelled"}


@router.post("/item/{item_id}/cancel")
def cancel_order_item(request:Request,
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    

    item = (
        db.query(OrderItems)
        .join(Order)
        .filter(
            OrderItems.id == item_id,
            Order.user_id == current_user.id
        )
        .first()
    )

    if not item:
        raise HTTPException(404)

    if item.status not in ["PLACED", "ACCEPTED"]:
        raise HTTPException(
            400,
            "This item cannot be cancelled"
        )
    
    restore_stock_for_item(item, db)

    refund_order_item(item, db)

    item.status = "CANCELLED"
    db.commit()

    return {"message": "Item cancelled"}



def refund_order_item(item, db):

    order = db.query(Order).filter(
        Order.id == item.order_id
    ).first()

    if not order or order.status != "PAID":
        return  

    payment = db.query(Payment).filter(
        Payment.order_id == order.id
    ).with_for_update().first()

    if not payment:
        return

    refund_amount = item.price_at_purchase * item.quantity

    
    if payment.amount < refund_amount:
        return

    payment.amount -= refund_amount

    if payment.amount == 0:
        payment.status = "REFUNDED"
    else:
        payment.status = "PARTIALLY_REFUNDED"

def restore_stock_for_item(item, db):
    product = db.query(Product).filter(
        Product.id == item.product_id
    ).with_for_update().first()

    if not product:
        return

    product.stock += item.quantity
