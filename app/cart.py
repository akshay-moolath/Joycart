from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Cart, CartItem, Product, User
from app.schemas import CartAdd, CartOut
from app.auth import get_current_user

router = APIRouter()

@router.post("/add", response_model=CartOut)
def add_to_cart(
    payload: CartAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1️⃣ Check product exists
    product = db.query(Product).filter(Product.id == payload.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # 2️⃣ Get or create cart
    cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()
    if not cart:
        cart = Cart(user_id=current_user.id)
        db.add(cart)
        db.commit()
        db.refresh(cart)

    # 3️⃣ Check if item already in cart
    item = (
        db.query(CartItem)
        .filter(
            CartItem.cart_id == cart.id,
            CartItem.product_id == payload.product_id
        )
        .first()
    )

    if item:
        item.quantity += payload.quantity
    else:
        item = CartItem(
            cart_id=cart.id,
            product_id=payload.product_id,
            quantity=payload.quantity
        )
        db.add(item)

    db.commit()
    db.refresh(cart)

    return cart


@router.patch("/item/{item_id}")
def update_quantity(
    item_id: int,
    quantity: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    item = (
    db.query(CartItem)
    .join(Cart)
    .filter(
        CartItem.id == item_id,
        Cart.user_id == current_user.id
    )
    .first()
)


    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    item.quantity = quantity
    db.commit()

    return {"message": "Quantity updated"}

