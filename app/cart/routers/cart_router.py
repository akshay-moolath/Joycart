from fastapi import APIRouter, Depends, HTTPException, Request,Form
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.db.db import get_db
from app.auth import get_current_user
from app.db.models import Cart, CartItem, User
from app.cart.services.cart_service import add_to_carts,get_carts,update_quantity,delete_quantity,cart_count,is_in_cart


router = APIRouter()
pages_router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.post("/add")
def add_to_cart(
    product_id: int = Form(...),
    quantity: int = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    
    return add_to_carts(product_id,quantity,current_user,db)

@router.get("/view")
def get_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_carts(current_user,db)


@router.patch("/item/{item_id}")
def update_quantity_endpoint(request: Request,
    item_id: int,
    quantity: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    
):
    
    return update_quantity(item_id,quantity,current_user,db)



@router.delete("/item/{item_id}")
def delete_quantity_endpoint(request: Request,
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    
):
    return delete_quantity(item_id,current_user)
    


@pages_router.get("/cart")
def viewcart(request: Request,
             current_user: User = Depends(get_current_user)):   
    return templates.TemplateResponse(
        "viewcart.html",
        {"request":request,
         "current_user":current_user}
    )



@pages_router.get("/cart/count")
def cart_count_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return cart_count(current_user,db)



@pages_router.get("/cart/exist/{product_id}")
def is_in_cart_endpoint(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return is_in_cart(product_id,current_user,db)