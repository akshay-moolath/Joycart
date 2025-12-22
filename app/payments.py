from fastapi import APIRouter, HTTPException,Request
from sqlalchemy.orm import Session
from fastapi import Depends
from app.db import get_db
from fastapi.templating import Jinja2Templates
from app.models import Order,OrderItems,Product,Payment
import uuid



router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.post("")
def payment(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.status=="PAID":
        raise HTTPException(status_code=400, detail="Already Paid")
    
    items = db.query(OrderItems).filter(OrderItems.order_id == order.id).all()

    for item in items:
        product = db.query(Product).filter(Product.id == item.product_id).first()

        if product.stock < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for {product.title}"
            )

        product.stock -= item.quantity
    payment = Payment(
        order_id=order.id,
        amount=order.amount,
        status="success",
        gateway="mock",
        gateway_payment_id= f"MOCK-{uuid.uuid4().hex[:12]}"
    )

    db.add(payment)
    order.status = "PAID"
    db.commit()

    return {
        "message": "payment successful",
        "order_id": order.id,
        "payment_id": payment.id,
        "status": order.status
    }


@router.get("/status/{order_id}")
def payment_success(request: Request, order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()

    if order.status == "PAID":
        details = "Payment Success"
    elif order.status == "REFUNDED":
        details = "Refund Success"
    else:
        details = "Order Cancelled"

    return templates.TemplateResponse(
        "payment_status.html",
        {   "request":request,
            "status": order.status,
            "details": details
            
        }
    )
