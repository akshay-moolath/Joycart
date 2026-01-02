from fastapi import APIRouter,Request,Form,Depends,HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.db.db import get_db
import os,uuid,hmac,hashlib
from app.db.models import Checkout
from app.checkout.helper import helper



pages_router = APIRouter()
router = APIRouter()

PAYMENT_WEBHOOK_SECRET = os.getenv("PAYMENT_WEBHOOK_SECRET")

if not PAYMENT_WEBHOOK_SECRET:
    raise RuntimeError("PAYMENT_WEBHOOK_SECRET is not set")


templates = Jinja2Templates(directory="templates")


@router.post("/checkout/payonline/confirmselected")
def confirm_payonline_method(
    request:Request,
    checkout_id: str = Form(...),
    method: str = Form(...),
    amount:str = Form(...)
):
    return RedirectResponse(
        f"/checkout/payonline/gateway?checkout_id={checkout_id}&method={method}&amount={amount}",
        status_code=302
    )


@pages_router.get("/checkout/payonline/confirm")
def payonline_payment_page(
    request: Request,
    checkout_id: str,
    method:str,
    db: Session = Depends(get_db)
):
    checkout = db.query(Checkout).filter(
        Checkout.checkout_id == checkout_id
    ).first()

    if not checkout:
        raise HTTPException(404)

    return templates.TemplateResponse(
        "payonline_confirm.html",
        {
            "request": request,
            "checkout_id": checkout_id,
            "amount": checkout.amount,
            "method":method
        }
    )

@router.post("/checkout/payonline/confirm")
def start_payonline_payment(
    checkout_id: str = Form(...),
    method:str = Form(...)
):
    return RedirectResponse(
        f"/checkout/payonline/gateway?checkout_id={checkout_id}&method={method}",
        status_code=302
    )

@pages_router.get("/checkout/payonline/gateway")
def payonline_gateway_page(
    request: Request,
    checkout_id: str,
    method:str
):
    
    gateway_payment_id = f"PAY-{uuid.uuid4().hex[:12]}"
    payload = f"{checkout_id}|SUCCESS|{gateway_payment_id}"
    signature = generate_signature(payload, PAYMENT_WEBHOOK_SECRET)

    return templates.TemplateResponse(
        "payonline_gateway.html",
        {
            "request": request,
            "checkout_id": checkout_id,
            "signature": signature,
            "gateway_payment_id":gateway_payment_id,
            "method":method
        }
    )

@router.post("/checkout/prepaid/webhook")
def payment_webhook(request:Request,
    checkout_id: str = Form(...),
    payment_status: str = Form(...),
    signature: str = Form(...),
    gateway_payment_id: str = Form(...),
    method:str =Form(...),
    db: Session = Depends(get_db)
):
    current_user = request.state.user

    payload = f"{checkout_id}|{payment_status}|{gateway_payment_id}"

    expected_signature = generate_signature(
        payload,
        PAYMENT_WEBHOOK_SECRET
    )

    if not hmac.compare_digest(signature, expected_signature):
        raise HTTPException(403, "Invalid signature")
    
    if payment_status != "SUCCESS":
        raise HTTPException(400, "Payment failed")

    helper(current_user,db,checkout_id,method,gateway_payment_id)

    return RedirectResponse("/checkout/prepaid/success", status_code=302)

@pages_router.get("/checkout/prepaid/success")
def payment_success(request:Request):

    return templates.TemplateResponse(
        "payonline_success.html",
        {
            "request": request
            }
    )


def generate_signature(payload: str, secret: str) -> str:
    return hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()