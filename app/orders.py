from fastapi import APIRouter, Depends, HTTPException,Request
from sqlalchemy.orm import Session
from app.db.db import get_db
from fastapi.templating import Jinja2Templates
from app.db.models import Order, OrderItems, Product,Payment, User,Refund
from app.auth import get_current_user
from app.checkout.checkout import razorpay_client 
from decimal import Decimal, ROUND_HALF_UP




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
        "shipping_address":order.shipping_address,
        "items": [
    {
        "item_id": oi.id,
        "product_id": product.id,
        "title": product.title,
        "price": oi.price_at_purchase,
        "quantity": oi.quantity,
        "status": oi.status,
        "refund_status": (
            db.query(Refund.status)
            .filter(Refund.orderitem_id == oi.id)
            .order_by(Refund.created_at.desc())
            .scalar()
        ),
        "subtotal": f"{(oi.price_at_purchase * oi.quantity):.2f}",
        "thumbnail": product.thumbnail
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


@router.get("/item/{item_id}")
def get_single_order_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = (
        db.query(OrderItems, Order, Product)
        .join(Order, Order.id == OrderItems.order_id)
        .join(Product, Product.id == OrderItems.product_id)
        .filter(
            OrderItems.id == item_id,
            Order.user_id == current_user.id
        )
        .first()
    )

    if not row:
        raise HTTPException(status_code=404, detail="Order item not found")

    oi, order, product = row

    refund_status = (
        db.query(Refund.status)
        .filter(Refund.orderitem_id == oi.id)
        .order_by(Refund.created_at.desc())
        .scalar()
    )

    payment = (
        db.query(Payment)
        .filter(Payment.order_id == order.id)
        .order_by(Payment.created_at.desc())
        .first()
    )

    return {
        "item": {
            "item_id": oi.id,
            "order_id": order.id,
            "product_id": product.id,
            "title": product.title,
            "price": oi.price_at_purchase,
            "quantity": oi.quantity,
            "status": oi.status,
            "refund_status": refund_status,
            "subtotal": f"{oi.price_at_purchase * oi.quantity:.2f}",
            "thumbnail": product.thumbnail,
        },
        "order": {
            "status": order.status,
            "created_at": order.created_at,
            "shipping_address": order.shipping_address,
        },
        "payment": (
            {
                "method": payment.method,
                "status": payment.status,
                "gateway_id": payment.gateway_payment_id,
            }
            if payment
            else None
        ),
    }


@pages_router.get("/orders")
def get_all_order_items(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    rows = (
        db.query(OrderItems, Order, Product)
        .join(Order, Order.id == OrderItems.order_id)
        .join(Product, Product.id == OrderItems.product_id)
        .filter(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
        .all()
    )

    order_items = [
        {   
            "item_id":oi.id,
            "order_id": order.id,
            "title": product.title,
            "thumbnail": product.thumbnail,
            "quantity": oi.quantity,
            "status": oi.status,
            "subtotal": f"{oi.price_at_purchase * oi.quantity:.2f}",
            "placed_at": order.created_at.strftime("%b %d, %Y"),
        }
        for oi, order, product in rows
    ]

    return templates.TemplateResponse(
        "orders.html",
        {
            "request": request,
            "order_items": order_items,
            "current_user": current_user
        }
    )

@pages_router.get("/orders/{order_id}/{item_id}")
def order_detail_page(request: Request,
    current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse(
        "orderdetails.html",
        {"request": request,
         "current_user":current_user}
    )


#######################################CANCEL AND REFUND ORDERS###################################
@router.post("/item/{item_id}/cancel")
def cancel_order_item(
    request: Request,
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        
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

        if item.status == "CANCELLED":
            return {"message": "Item already cancelled"}

        if item.status not in ["PLACED", "CONFIRMED"]:
            raise HTTPException(400, "This item cannot be cancelled")
        

        payment = (
        db.query(Payment)
        .filter(
            Payment.order_id == item.order_id
        )
        .first()
    )
        item.status = "CANCELLED"

        restore_stock_for_item(item, db)

        if payment.method == "COD":
            payment.status = "NOT_REQUIRED"

        else:
            existing_refund = db.query(Refund).filter(
                Refund.orderitem_id == item.id
            ).first()

            if not existing_refund:
                refund = create_refund_record(item, payment, db)
                db.flush()
                initiate_razorpay_refund(refund, db)
                
        db.commit()
        return {"message": "Item cancelled"}

    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))

def create_refund_record(item,payment,db):

    if not payment:
        return None
    
    
    refund = Refund(
            payment_id=payment.id,
            gateway_payment_id=payment.gateway_payment_id,
            amount = Decimal(item.price_at_purchase) * Decimal(item.quantity),
            reason="ITEM_CANCELLED",
            status="INITIATED",
            orderitem_id=item.id
        )


    db.add(refund)
    return refund

def initiate_razorpay_refund(refund, db):
    if not refund:
        return

    try:
        amount_paise = int(
            (refund.amount * Decimal("100"))
            .quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        )

        razorpay_refund = razorpay_client.payment.refund(
            refund.gateway_payment_id,
            {
                "amount": amount_paise,
                "notes": {"order_item_id": refund.orderitem_id}
            }
        )

        refund.gateway_refund_id = razorpay_refund["id"]
        refund.status = "PROCESSING"

    except Exception as e:
        refund.status = "FAILED"
        raise

def restore_stock_for_item(item, db):
    product = db.query(Product).filter(
        Product.id == item.product_id
    ).first()

    if not product:
        return

    product.stock += item.quantity

