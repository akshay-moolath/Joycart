from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.db.db import get_db
from app.db.models import Cart,Product,Checkout,Address,CheckoutItem,User,Order,CartItem,Refund
from datetime import datetime
import uuid, razorpay ,os,hmac,hashlib,json
from sqlalchemy.exc import SQLAlchemyError
from decimal import Decimal, ROUND_HALF_UP
from app.checkout.helper import helper
from app.auth import get_current_user



router = APIRouter()
pages_router = APIRouter()
razorpay_router = APIRouter() #for razorpay to avoid unauthorization

templates = Jinja2Templates(directory="templates")

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET")

razorpay_client = razorpay.Client(
    auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)
)


@router.post("/checkout/start")
def start_checkout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        lazy_cleanup_checkouts(db)

        cart = db.query(Cart).filter(
            Cart.user_id == current_user.id
        ).first()

        if not cart or not cart.items:
            raise HTTPException(400, "Cart is empty")
        
        cart_items = (db.query(CartItem).filter(
                        CartItem.cart_id == cart.id
                    ).all())

        if not cart_items:
            raise HTTPException(400, "Cart is empty")

        product_ids = [item.product_id for item in cart.items]

        products = db.query(Product).filter(
            Product.id.in_(product_ids)
        ).all()

        product_map = {p.id: p for p in products}

        total_amount = 0
        for item in cart.items:

            product = product_map[item.product_id]

            if product.seller_id == current_user.seller_id:
                raise HTTPException(
                    status_code=400,
                    detail="You cannot checkout your own product"
                )
            
            if product.stock < item.quantity:
                raise HTTPException(
                    400,
                    f"Insufficient stock for {product.title}"
                )
            
            total_amount += product.price * item.quantity

            if total_amount <= 0:
                raise HTTPException(400, "Invalid checkout")

        checkout = Checkout(
            checkout_id=str(uuid.uuid4()),
            user_id=current_user.id,
            amount=total_amount,
            mode="CART",
            status="CREATED"
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

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(500, "Checkout start failed")

@router.post("/checkout/buy-now")
def buy_now(
    request: Request,
    product_id: int = Form(...),
    quantity: int = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(404, "Product not found")
        
        
        
        if product.seller_id == current_user.seller_id:
            raise HTTPException(
                status_code=400,
                detail="You cannot buy your own product"
            )

        checkout = Checkout(
            checkout_id=str(uuid.uuid4()),
            user_id=current_user.id,
            amount=product.price * quantity,
            mode="BUY NOW",
            status="CREATED"
        )

        db.add(checkout)
        db.flush()

        checkout_item = CheckoutItem(
            checkout_id=checkout.id,
            product_id=product.id,
            quantity=quantity,
            price_at_checkout=product.price
        )

        if product.stock < checkout_item.quantity:
                raise HTTPException(
                    400,
                    f"Insufficient stock for {product.title}"
                )

        db.add(checkout_item)
        db.commit()

        return {
            "redirect_url": f"/checkout/address?checkout_id={checkout.checkout_id}"
        }
    except SQLAlchemyError:
            db.rollback()
            raise HTTPException(500, "Buy Now failed")


@pages_router.get("/checkout/address")
def checkout_address_page(
    request: Request,
    checkout_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    
    lazy_cleanup_checkouts(db)

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
            "checkout_id": checkout_id,
            "current_user":current_user
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
    lazy_cleanup_checkouts(db)

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
            "checkout_id": checkout_id,
            "current_user":current_user
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
    lazy_cleanup_checkouts(db)
    
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
            "amount": checkout.amount,
            "current_user":current_user
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
        f"/checkout/payonline?checkout_id={checkout_id}",
        status_code=302
    )

@pages_router.get("/checkout/payonline")
def payonline(
    request:Request,
    checkout_id: str,
):
    return templates.TemplateResponse(
        "payonline_gateway.html",{
            "request":request,
            "checkout_id":checkout_id         
        }
    )


@router.post("/checkout/payonline/create")
def create_payonline_checkout(
    checkout_id: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    lazy_cleanup_checkouts(db)

    checkout = db.query(Checkout).filter(
        Checkout.checkout_id == checkout_id,
        Checkout.user_id == current_user.id
    ).first()

    if not checkout:
        raise HTTPException(404, "Invalid checkout")
    
    checkout_items = db.query(CheckoutItem).filter(
            CheckoutItem.checkout_id == checkout.id
        ).all()

    if not checkout_items:
        raise HTTPException(400, "No checkout items")

    amount_paise = int(
        (Decimal(str(checkout.amount)) * 100)
        .quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    )

    razorpay_order = razorpay_client.order.create({
        "amount": amount_paise,
        "currency": "INR",
        "receipt": checkout.checkout_id,
        "payment_capture": 1
    })

    checkout.gateway_order_id = razorpay_order["id"]

    checkout.status = "PAYMENT_INITIATED"

    db.commit()

    return {
        "key": RAZORPAY_KEY_ID,
        "order_id": razorpay_order["id"],
        "amount": amount_paise,
        "currency": "INR"
    }

@razorpay_router.post("/checkout/payonline/webhook")
async def razorpay_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature")

    expected = hmac.new(
        RAZORPAY_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature, expected):
        return {"status": "ignored"}

    payload = json.loads(body)
    event = payload.get("event")

    
    if event == "payment.captured":
        payment = payload["payload"]["payment"]["entity"]

        razorpay_order_id = payment["order_id"]
        razorpay_payment_id = payment["id"]
        method = payment["method"]

        checkout = db.query(Checkout).filter(
            Checkout.gateway_order_id == razorpay_order_id
        ).first()

        if not checkout:
            return {"status": "ignored"}

        existing_order = db.query(Order).filter(
            Order.checkout_id == checkout.checkout_id
        ).first()

        if existing_order:
            return {"status": "already_processed"}

        user = db.query(User).filter(
            User.id == checkout.user_id
        ).first()

        if not user:
            return {"status": "ignored"}

        helper(
            user,
            db,
            checkout.checkout_id,
            method,
            razorpay_payment_id
        )

        return {"status": "payment_processed"}

    
    if event in ("refund.processed", "refund.failed"):
        refund_entity = payload["payload"]["refund"]["entity"]
        razorpay_refund_id = refund_entity["id"]

        refund = db.query(Refund).filter(
            Refund.gateway_refund_id == razorpay_refund_id
        ).first()

        if not refund:
            return {"status": "refund_not_found"}

        refund.status = (
            "REFUNDED" if event == "refund.processed" else "FAILED"
        )

        db.commit()
        
        return {"status": "refund_updated"}

    return {"status": "ignored"}


        


@pages_router.get("/checkout/payonline/waiting")
def payonline_waiting_page(
    request: Request
):
    return templates.TemplateResponse(
        "payonline_success.html",
        {
            "request": request
        }
    )


def lazy_cleanup_checkouts(db):
    now = datetime.utcnow()

    expired_checkouts = db.query(Checkout).filter(
    Checkout.expires_at < now,
    Checkout.status.in_(["CREATED"])
).all()

    for checkout in expired_checkouts:
        
        db.query(CheckoutItem).filter(
            CheckoutItem.checkout_id == checkout.id
        ).delete(synchronize_session=False)

        
        db.delete(checkout)

    db.commit()
