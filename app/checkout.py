from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.db import get_db
from fastapi import Header
import os
from datetime import datetime,timedelta
from app.models import Cart,Payment,Product,Checkout,OrderItems,Address,CartItem,Order
import uuid

router = APIRouter()
pages_router = APIRouter()

_last_cleanup = None

templates = Jinja2Templates(directory="templates")

@router.post("/checkout/start")
def start_checkout(
    request: Request,
    db: Session = Depends(get_db)
):
    current_user = request.state.user

    lazy_cleanup_checkouts(db)

    cart = db.query(Cart).filter(
        Cart.user_id == current_user.id
    ).first()

    if not cart or not cart.items:
        raise HTTPException(400, "Cart is empty")

    total_amount = 0
    for item in cart.items:
        product = db.query(Product).filter(
            Product.id == item.product_id
        ).first()
        total_amount += product.price * item.quantity

    checkout = Checkout(
        checkout_id=str(uuid.uuid4()),
        user_id=current_user.id,
        amount=total_amount
    )

    db.add(checkout)
    db.commit()

    return {
        "redirect_url": f"/checkout/address?checkout_id={checkout.checkout_id}"
    }

@router.post("/checkout/address")
def save_checkout_address(
    request:Request,
    checkout_id: str = Form(...),
    selected_address_id: int = Form(...),
    db: Session = Depends(get_db)
):
    current_user = request.state.user

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
    db: Session = Depends(get_db)
):
    current_user = request.state.user
    
    checkout = db.query(Checkout).filter(
        Checkout.checkout_id == checkout_id,
        Checkout.user_id == current_user.id
    ).first()

    if not checkout or not checkout.shipping_address:
        raise HTTPException(400)

    cart = db.query(Cart).filter(
        Cart.user_id == current_user.id
    ).first()

    if not cart:
        raise HTTPException(400, "Cart not found")

    items = (
        db.query(CartItem, Product)
        .join(Product, Product.id == CartItem.product_id)
        .filter(CartItem.cart_id == cart.id)
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
@pages_router.get("/checkout/address")
def checkout_address_page(
    request: Request,
    checkout_id: str,
    db: Session = Depends(get_db)
):
    
    current_user = request.state.user

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
        "address_delivery.html",
        {
            "request": request,
            "addresses": addresses,
            "checkout_id": checkout_id
        }
    )

@pages_router.get("/checkout/payment")
def checkout_payment_page(
    request: Request,
    checkout_id: str,
    db: Session = Depends(get_db)
):
    current_user = request.state.user
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
    payment_method: str = Form(...),
    db: Session = Depends(get_db)
):
    current_user = request.state.user

    checkout = db.query(Checkout).filter(
        Checkout.checkout_id == checkout_id,
        Checkout.user_id == current_user.id
    ).first()

    if not checkout:
        raise HTTPException(404)

    checkout.payment_method = payment_method
    db.commit()


    if payment_method == "COD":
        return RedirectResponse(
            f"/checkout/cod/confirm?checkout_id={checkout_id}",
            status_code=302
        )

    
    return RedirectResponse(
        f"/payment/start?checkout_id={checkout_id}",
        status_code=302
    )

@pages_router.get("/checkout/cod/confirm")
def cod_confirm_page(
    request: Request,
    checkout_id: str
):
    current_user = request.state.user
    return templates.TemplateResponse(
        "cod_confirm.html",
        {
            "request": request,
            "checkout_id": checkout_id
        }
    )

@router.post("/checkout/cod/confirm")
def place_cod_order(
    request: Request,
    checkout_id: str = Form(...),
    db: Session = Depends(get_db)
):
    current_user = request.state.user

    checkout = db.query(Checkout).filter(
        Checkout.checkout_id == checkout_id,
        Checkout.user_id == current_user.id
    ).first()
    if not checkout:
        raise HTTPException(404)
    
    existing_order = db.query(Order).filter(
            Order.checkout_id == checkout.checkout_id
        ).first()

    if existing_order:
        return RedirectResponse(
            "/checkout/cod/orderplace",
            status_code=302
        )

    cart = db.query(Cart).filter(
        Cart.user_id == current_user.id
    ).first()
    if not cart or not cart.items:
        raise HTTPException(400, "Cart is empty")

    total_amount = 0
    order_items = []
    
    product_ids = [item.product_id for item in cart.items]
    products = (
        db.query(Product)
        .filter(Product.id.in_(product_ids))
        .with_for_update()
        .all()
    )
    product_map = {p.id: p for p in products}

    for item in cart.items:
        product = product_map.get(item.product_id)

        if not product:
            continue

        if product.stock < item.quantity:
            raise HTTPException(
                400, f"Insufficient stock for {product.title}"
            )

        subtotal = product.price * item.quantity
        total_amount += subtotal

        product.stock -= item.quantity

        order_items.append(
            OrderItems(
                product_id=product.id,
                quantity=item.quantity,
                seller_id=product.seller_id,
                price_at_purchase=product.price
            )
        )


    if total_amount == 0:
        raise HTTPException(400, "Invalid cart")

    order = Order(
        user_id=current_user.id,
        amount=total_amount,
        checkout_id=checkout.checkout_id,
        shipping_address=checkout.shipping_address,
        status="PLACED",
        currency="INR"
    )

    db.add(order)
    db.flush()   

    for oi in order_items:
        oi.order_id = order.id

    payment = Payment(
        order_id=order.id,
        amount=order.amount,
        status="DUE",
        method="COD"
    )

    db.add_all(order_items)
    db.add(payment)

    
    db.query(CartItem).filter(
        CartItem.cart_id == cart.id
    ).delete()

    db.delete(checkout)
    db.commit()

    return RedirectResponse(
        "/checkout/cod/orderplace",
        status_code=302
    )
@pages_router.get("/checkout/cod/orderplace")
def cod_order_success(request:Request):
    return templates.TemplateResponse(
        "cod_order_success.html",
        {"request":request}
    )

@pages_router.get("/payment/start")
def payment_start_page(
    request: Request,
    checkout_id: str
):
    return templates.TemplateResponse(
        "payment_start.html",
        {
            "request": request,
            "checkout_id": checkout_id
        }
    )
@router.post("/payment/process")
def payment_process(
    request:Request,
    checkout_id: str = Form(...),
    db: Session = Depends(get_db)
):
    current_user = request.state.user

    return RedirectResponse(
        f"/payment/success?checkout_id={checkout_id}",
        status_code=302
    )

@pages_router.get("/checkout/prepaid/confirm")
def prepaid_payment_page(
    request: Request,
    checkout_id: str,
    db: Session = Depends(get_db)
):
    checkout = db.query(Checkout).filter(
        Checkout.checkout_id == checkout_id
    ).first()

    if not checkout:
        raise HTTPException(404)

    return templates.TemplateResponse(
        "payment_gateway.html",
        {
            "request": request,
            "checkout_id": checkout_id,
            "amount": checkout.amount
        }
    )
@router.post("/checkout/prepaid/confirm")
def payment_success(request: Request,
    checkout_id: str = Form(...),
    db: Session = Depends(get_db)
):
    current_user = request.state.user

    checkout = db.query(Checkout).filter(
        Checkout.checkout_id == checkout_id,
        Checkout.user_id == current_user.id
    ).first()

    if not checkout:
        raise HTTPException(404)
    
    existing_order = db.query(Order).filter(
        Order.checkout_id == checkout.checkout_id
    ).first()

    if existing_order:
        return RedirectResponse(
        "/payment/success",
        status_code=302
    )

    cart = db.query(Cart).filter(
        Cart.user_id == current_user.id
    ).first()
    if not cart or not cart.items:
        raise HTTPException(400, "Cart is empty")

    total_amount = 0
    order_items = []
    
    product_ids = [item.product_id for item in cart.items]
    products = (
        db.query(Product)
        .filter(Product.id.in_(product_ids))
        .with_for_update()
        .all()
    )
    product_map = {p.id: p for p in products}

    for item in cart.items:
        product = product_map.get(item.product_id)

        if not product:
            continue

        if product.stock < item.quantity:
            raise HTTPException(
                400, f"Insufficient stock for {product.title}"
            )

        subtotal = product.price * item.quantity
        total_amount += subtotal

        product.stock -= item.quantity

        order_items.append(
            OrderItems(
                product_id=product.id,
                quantity=item.quantity,
                seller_id=product.seller_id,
                price_at_purchase=product.price
            )
        )


    if total_amount == 0:
        raise HTTPException(400, "Invalid cart")

    order = Order(
        user_id=current_user.id,
        amount=total_amount,
        checkout_id=checkout.checkout_id,
        shipping_address=checkout.shipping_address,
        status="PAID",
        currency="INR"
    )

    db.add(order)
    db.flush()   

    for oi in order_items:
        oi.order_id = order.id

    payment = Payment(
        order_id=order.id,
        amount=order.amount,
        status="PAID",
        method="PREPAID",
        gateway_payment_id= f"PAY-{uuid.uuid4().hex[:12]}"
    )

    db.add_all(order_items)
    db.add(payment)

    
    db.query(CartItem).filter(
        CartItem.cart_id == cart.id
    ).delete()

    db.delete(checkout)
    db.commit()

    return RedirectResponse("/payment/success",
        status_code=302
    )

@pages_router.get("/payment/success")
def payment_success(request:Request):

    return templates.TemplateResponse(
        "prepaid_success.html",
        {
            "request": request
            }
    )

def lazy_cleanup_checkouts(db):
    global _last_cleanup

    now = datetime.utcnow()

    if _last_cleanup and now - _last_cleanup < timedelta(minutes=10):
        return

    db.query(Checkout).filter(
        Checkout.expires_at < now
    ).delete()

    db.commit()
    _last_cleanup = now