from fastapi import APIRouter, Depends, HTTPException, status, Request,Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Seller
from app.schemas import SellerCreate, SellerOut
from app.models import User

router = APIRouter()

@router.post("/seller/register")
def register_seller(request: Request,store_name: str = Form(...),db: Session = Depends(get_db)):
    current_user = request.state.user
    existing_seller = (
        db.query(Seller)
        .filter(Seller.user_id == current_user.id)
        .first()
    )

    if existing_seller:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a seller"
        )

    seller = Seller(
        user_id=current_user.id,
        store_name=store_name
    )

    db.add(seller)
    db.commit()
    db.refresh(seller)

    return RedirectResponse("/seller/dashboard", status_code=302)