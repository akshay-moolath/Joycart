from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.db.db import get_db
from app.db.models import Cart,Product,Checkout,Address,CheckoutItem,User
from datetime import datetime
import uuid
from app.auth import get_current_user

router = APIRouter()
pages_router = APIRouter()

_last_cleanup = None #lazy cleanup 



templates = Jinja2Templates(directory="templates")

@router.post("/checkout/start")
def start_checkout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    lazy_cleanup_checkouts(db)

    cart = db.query(Cart).filter(
        Cart.user_id == current_user.id
    ).first()

    if not cart or not cart.items:
        raise HTTPException(400, "Cart is empty")

    product_ids = [item.product_id for item in cart.items]

    products = db.query(Product).filter(
        Product.id.in_(product_ids)
    ).all()

    product_map = {p.id: p for p in products}

    total_amount = 0
    for item in cart.items:
        product = product_map[item.product_id]
        total_amount += product.price * item.quantity

    checkout = Checkout(
        checkout_id=str(uuid.uuid4()),
        user_id=current_user.id,
        amount=total_amount,
        mode="CART"
    )

    db.add(checkout)
    db.flush()  

    for item in cart.items:
        product = product_map[item.product_id]
        checkout_item = CheckoutItem(
            checkout_id=checkout.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price_at_checkout=product.price
        )
        db.add(checkout_item)

    db.commit()

    return {
        "redirect_url": f"/checkout/address?checkout_id={checkout.checkout_id}"
    }

@router.post("/checkout/buy-now")
def buy_now(
    request: Request,
    product_id: int = Form(...),
    quantity: int = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(404, "Product not found")

    checkout = Checkout(
        checkout_id=str(uuid.uuid4()),
        user_id=current_user.id,
        amount=product.price * quantity,
        mode="BUY NOW"
    )

    db.add(checkout)
    db.flush()

    checkout_item = CheckoutItem(
        checkout_id=checkout.id,
        product_id=product.id,
        quantity=quantity,
        price_at_checkout=product.price
    )

    db.add(checkout_item)
    db.commit()

    return {
        "redirect_url": f"/checkout/address?checkout_id={checkout.checkout_id}"
    }


@pages_router.get("/checkout/address")
def checkout_address_page(
    request: Request,
    checkout_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    

    checkout = db.query(Checkout).filter(
        Checkout.checkout_id == checkout_id,
        Checkout.user_id == current_user.id
    ).first()

    if not checkout:
        raise HTTPException(404)

    addresses = db.query(Address).filter(
        Address.user_id == current_user.id
    ).all()

    return templates.TemplateResponse(
        "checkout_delivery_address.html",
        {
            "request": request,
            "addresses": addresses,
            "checkout_id": checkout_id
        }
    )

@router.post("/checkout/address")
def save_checkout_address(
    request:Request,
    checkout_id: str = Form(...),
    selected_address_id: int = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
 

    checkout = db.query(Checkout).filter(
        Checkout.checkout_id == checkout_id,
        Checkout.user_id == current_user.id
    ).first()

    if not checkout:
        raise HTTPException(404)

    address = db.query(Address).filter(
        Address.id == selected_address_id,
        Address.user_id == current_user.id
    ).first()

    checkout.shipping_address = {
        "name": address.name,
        "phone": address.phone,
        "address_line1": address.address_line1,
        "city": address.city,
        "state": address.state,
        "pincode": address.pincode
    }

    db.commit()

    return RedirectResponse(
        f"/checkout/summary?checkout_id={checkout_id}",
        status_code=302
    )

@pages_router.get("/checkout/summary")
def checkout_summary(
    request: Request,
    checkout_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    checkout = db.query(Checkout).filter(
        Checkout.checkout_id == checkout_id,
        Checkout.user_id == current_user.id
    ).first()

    if not checkout or not checkout.shipping_address:
        raise HTTPException(400)

    items = (
        db.query(CheckoutItem, Product)
        .join(Product, Product.id == CheckoutItem.product_id)
        .filter(CheckoutItem.checkout_id == checkout.id)
        .all()
    )

    return templates.TemplateResponse(
        "checkout_summary.html",
        {
            "request": request,
            "checkout": checkout,
            "items": items,
            "checkout_id": checkout_id
        }
    )

    
             

@router.post("/checkout/confirm")
def confirm_checkout(
    checkout_id: str = Form(...),
    db: Session = Depends(get_db)
):
    
    return RedirectResponse(
        f"/checkout/payment?checkout_id={checkout_id}",
        status_code=302
    )


@pages_router.get("/checkout/payment")
def checkout_payment_page(
    request: Request,
    checkout_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    
    
    checkout = db.query(Checkout).filter(
        Checkout.checkout_id == checkout_id,
        Checkout.user_id == current_user.id
    ).first()

    if not checkout or not checkout.shipping_address:
        raise HTTPException(400, "Invalid checkout")

    return templates.TemplateResponse(
        "checkout_payment.html",
        {
            "request": request,
            "checkout_id": checkout_id,
            "amount": checkout.amount
        }
    )



@router.post("/checkout/payment")
def select_payment_method(
    request:Request,
    checkout_id: str = Form(...),
    method: str = Form(...),
    amount:str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    checkout = db.query(Checkout).filter(
        Checkout.checkout_id == checkout_id,
        Checkout.user_id == current_user.id
    ).first()

    if not checkout:
        raise HTTPException(404)

    
    db.commit()


    if method == "COD":
        return RedirectResponse(
            f"/checkout/cod/confirm?checkout_id={checkout_id}",
            status_code=302
        )

    return RedirectResponse(
        f"/checkout/payonline/select?checkout_id={checkout_id}&method={method}&amount={amount}",
        status_code=302
    )

@pages_router.get("/checkout/payonline/select")
def select_payonline_method(
    request:Request,
    checkout_id: str,
    method: str,
    amount:str
):
    return templates.TemplateResponse(
        "payonline_select.html",{
            "request":request,
            "checkout_id":checkout_id,
            "method":method,
            "amount":amount
        }
    )

def lazy_cleanup_checkouts(db):
    now = datetime.utcnow()

    expired_checkouts = db.query(Checkout).filter(
        Checkout.expires_at < now
    ).all()

    for checkout in expired_checkouts:
        
        db.query(CheckoutItem).filter(
            CheckoutItem.checkout_id == checkout.id
        ).delete()

        
        db.delete(checkout)

    db.commit()

