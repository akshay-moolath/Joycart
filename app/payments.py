from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from fastapi import Depends

from app.db import get_db
from app.models import Order

router = APIRouter()

@router.post("")
def payment(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.status = "PAID"
    db.commit()

    return {
        "message": "Mock payment successful",
        "order_id": order.id,
        "status": order.status
    }
