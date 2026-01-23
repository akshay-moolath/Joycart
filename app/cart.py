from fastapi import APIRouter, Depends, HTTPException, Request,Form
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.db.db import get_db
from app.auth import get_current_user
from app.db.models import Cart, CartItem, Product, User


router = APIRouter()
pages_router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.post("/add")
def add_to_cart(request:Request,
    product_id: int = Form(...),
    quantity: int = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if product.seller_id == current_user.seller_id:
        raise HTTPException(
            status_code=400,
            detail="You cannot buy your own product"
        )

    
    cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()
    if not cart:
        cart = Cart(user_id=current_user.id)
        db.add(cart)
        db.commit()
        db.refresh(cart)

    
    item = (
        db.query(CartItem)
        .filter(
            CartItem.cart_id == cart.id,
            CartItem.product_id == product_id
        )
        .first()
    )

    if item:
        item.quantity += quantity
    else:
        item = CartItem(
            cart_id=cart.id,
            product_id=product_id,
            quantity=quantity
        )
        db.add(item)

    db.commit()
    db.refresh(cart)

    return cart


@router.get("/view")
def get_cart(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cart = (
        db.query(Cart)
        .filter(Cart.user_id == current_user.id)
        .first()
    )

    if not cart:
        return {"items": [], "total": 0}

    total = 0
    items = []

    cart_rows = (
        db.query(CartItem, Product)
        .join(Product, CartItem.product_id == Product.id)
        .filter(CartItem.cart_id == cart.id)
        .order_by(CartItem.id.asc())   
        .all()
    )

    for cart_item, product in cart_rows:
        subtotal = product.price * cart_item.quantity
        total += subtotal

        items.append({
            "id": cart_item.id,
            "product_id": product.id,
            "title": product.title,
            "price": product.price,
            "quantity": cart_item.quantity,
            "subtotal": subtotal,
            "thumbnail": product.thumbnail
        })

    return {
        "items": items,
        "total": total
    }


@router.patch("/item/{item_id}")
def update_quantity(request: Request,
    item_id: int,
    quantity: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    
):
    
    item = (db.query(CartItem).join(Cart).filter(CartItem.id == item_id,Cart.user_id == current_user.id).first())
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    item.quantity = quantity
    db.commit()

    return {"message": "Quantity updated"}



@router.delete("/item/{item_id}")
def delete_quantity(request: Request,
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    
):
    
    item = (db.query(CartItem).join(Cart).filter(CartItem.id == item_id,Cart.user_id == current_user.id).first())
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()

    return {"message": "Item removed"}

@pages_router.get("/cart")
def viewcart(request: Request,
             current_user: User = Depends(get_current_user)):   
    return templates.TemplateResponse(
        "viewcart.html",
        {"request":request,
         "current_user":current_user}
    )



@pages_router.get("/cart/count")
def cart_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    cart = (
        db.query(Cart)
        .filter(Cart.user_id == current_user.id)
        .first()
    )


    if not cart:
        return {"count": 0}

    count = (
        db.query(CartItem)
        .filter(CartItem.cart_id == cart.id)
        .count()
    )

    return {"count": count}


@pages_router.get("/cart/exist/{product_id}")
def is_in_cart(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cart = (
        db.query(Cart)
        .filter(Cart.user_id == current_user.id)
        .first()
    )

    if not cart:
        return {"in_cart": False}

    exists = (
        db.query(CartItem)
        .filter(
            CartItem.cart_id == cart.id,
            CartItem.product_id == product_id
        )
        .first()
        is not None
    )

    return {"in_cart": exists}