from datetime import datetime
import logging
from app.db.models import (
    Checkout,
    CheckoutItem,
    Cart,
    CartItem,
    Product,
    Checkout,
    CheckoutItem,
    Address,
    Payment,
    Order,
    OrderItems,
)
import uuid, os, razorpay  # pylint: disable=no-member
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from decimal import Decimal, ROUND_HALF_UP

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
logger = logging.getLogger(__name__)


def cart_checkout(db: Session, current_user):
    try:

        lazy_cleanup_checkouts(db)

        cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()

        if not cart or not cart.items:
            raise HTTPException(400, "Cart is empty")

        cart_items = db.query(CartItem).filter(CartItem.cart_id == cart.id).all()

        if not cart_items:
            raise HTTPException(400, "Cart is empty")

        product_ids = [item.product_id for item in cart_items]

        products = db.query(Product).filter(Product.id.in_(product_ids)).all()

        product_map = {p.id: p for p in products}

        total_amount = 0

        for item in cart_items:
            product = product_map[item.product_id]

            if product.seller_id == current_user.seller_id:
                raise HTTPException(400, "You cannot checkout your own product")

            if product.stock < item.quantity:
                raise HTTPException(400, f"Insufficient stock for {product.title}")

            total_amount += product.price * item.quantity

        if total_amount <= 0:
            raise HTTPException(400, "Invalid checkout")

        checkout = Checkout(
            checkout_id=str(uuid.uuid4()),
            user_id=current_user.id,
            amount=total_amount,
            mode="CART",
            status="CREATED",
        )

        db.add(checkout)
        db.flush()

        for item in cart_items:
            product = product_map[item.product_id]
            checkout_item = CheckoutItem(
                checkout_id=checkout.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price_at_checkout=product.price,
            )
            db.add(checkout_item)

        db.commit()

        return checkout.checkout_id

    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(500, "Checkout start failed") from exc


def buy_now_checkout(db: Session, current_user, product_id: int, quantity: int):
    try:

        product = db.query(Product).filter(Product.id == product_id).first()

        if not product:
            raise HTTPException(404, "Product not found")

        if product.seller_id == current_user.seller_id:
            raise HTTPException(400, "You cannot buy your own product")

        if quantity <= 0:
            raise HTTPException(400, "Invalid quantity")

        if product.stock < quantity:
            raise HTTPException(400, f"Insufficient stock for {product.title}")

        checkout = Checkout(
            checkout_id=str(uuid.uuid4()),
            user_id=current_user.id,
            amount=product.price * quantity,
            mode="BUY_NOW",
            status="CREATED",
        )

        db.add(checkout)
        db.flush()

        checkout_item = CheckoutItem(
            checkout_id=checkout.id,
            product_id=product.id,
            quantity=quantity,
            price_at_checkout=product.price,
        )

        db.add(checkout_item)
        db.commit()

        return checkout.checkout_id

    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(500, "Buy Now failed") from exc


def get_checkout(db: Session, checkout_id: str, user_id: int):
    lazy_cleanup_checkouts(db)

    checkout = (
        db.query(Checkout)
        .filter(Checkout.checkout_id == checkout_id, Checkout.user_id == user_id)
        .first()
    )

    if not checkout:
        raise HTTPException(404, "Checkout not found")

    return checkout


def get_checkout_items(db, checkout):
    checkout_items = (
        db.query(CheckoutItem, Product)
        .join(Product, Product.id == CheckoutItem.product_id)
        .filter(CheckoutItem.checkout_id == checkout.id)
        .all()
    )
    if not checkout_items:
        raise HTTPException(400, "No checkout items")

    return checkout_items


def get_addresses(db: Session, user_id: int, selected_address_id: int):
    if selected_address_id:
        address = (
            db.query(Address)
            .filter(Address.id == selected_address_id, Address.user_id == user_id)
            .first()
        )
    else:
        address = db.query(Address).filter(Address.user_id == user_id).all()

    return address


def shipping_address(db, checkout, address):
    checkout.shipping_address = {
        "name": address.name,
        "phone": address.phone,
        "address_line1": address.address_line1,
        "city": address.city,
        "state": address.state,
        "pincode": address.pincode,
    }
    db.commit()


def lazy_cleanup_checkouts(db):
    now = datetime.utcnow()

    expired_checkouts = (
        db.query(Checkout)
        .filter(Checkout.expires_at < now, Checkout.status.in_(["CREATED"]))
        .all()
    )

    for checkout in expired_checkouts:

        db.query(CheckoutItem).filter(CheckoutItem.checkout_id == checkout.id).delete(
            synchronize_session=False
        )

        db.delete(checkout)

    db.commit()


def create_payonline_order(db: Session, checkout_id: str, user_id: int):

    lazy_cleanup_checkouts(db)

    checkout = get_checkout(db=db, checkout_id=checkout_id, user_id=user_id)

    get_checkout_items(db, checkout)

    if checkout.status not in ["CREATED"]:
        raise HTTPException(400, "Invalid checkout state")

    amount_paise = int(
        (Decimal(str(checkout.amount)) * 100).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
    )

    razorpay_order = razorpay_client.order.create(
        {
            "amount": amount_paise,
            "currency": "INR",
            "receipt": checkout.checkout_id,
            "payment_capture": 1,
        }
    )

    checkout.gateway_order_id = razorpay_order["id"]
    checkout.status = "PAYMENT_INITIATED"

    db.commit()

    return {
        "key": RAZORPAY_KEY_ID,
        "order_id": razorpay_order["id"],
        "amount": amount_paise,
        "currency": "INR",
    }


def place_order(current_user, db, checkout_id, method, razorpay_payment_id):
    try:
        checkout = (
            db.query(Checkout).filter(Checkout.checkout_id == checkout_id).first()
        )

        if not checkout:
            raise Exception("Checkout not found")

        checkout_items = (
            db.query(CheckoutItem).filter(CheckoutItem.checkout_id == checkout.id).all()
        )

        if not checkout_items:
            raise Exception("No checkout items")

        product_ids = [item.product_id for item in checkout_items]

        products = (
            db.query(Product)
            .filter(Product.id.in_(product_ids))
            .with_for_update()
            .all()
        )
        product_map = {p.id: p for p in products}

        order_items = []

        for item in checkout_items:
            product = product_map.get(item.product_id)

            if not product:
                raise Exception(f"Product missing: {item.product_id}")

            if product.stock < item.quantity:
                raise Exception(f"Stock issue after payment for product {product.id}")

            product.stock -= item.quantity

            order_items.append(
                OrderItems(
                    product_id=product.id,
                    quantity=item.quantity,
                    seller_id=product.seller_id,
                    price_at_purchase=item.price_at_checkout,
                    status="PLACED",
                )
            )

        order = Order(
            user_id=current_user.id,
            amount=checkout.amount,
            checkout_id=checkout.checkout_id,
            shipping_address=checkout.shipping_address,
            status="PLACED",
            currency="INR",
        )

        db.add(order)
        db.flush()

        for oi in order_items:
            oi.order_id = order.id

        if method == "COD":
            payment = Payment(
                order_id=order.id, amount=order.amount, status="PENDING", method="COD"
            )
        else:
            payment = Payment(
                order_id=order.id,
                amount=order.amount,
                status="SUCCESS",
                method=method.upper(),
                gateway_payment_id=razorpay_payment_id,
            )

        checkout.status = "COMPLETED"

        db.add_all(order_items)
        db.add(payment)

        db.query(CheckoutItem).filter(CheckoutItem.checkout_id == checkout.id).delete(
            synchronize_session=False
        )

        db.delete(checkout)

        cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()

        if cart:
            if checkout.mode == "CART":
                
                db.query(CartItem).filter(CartItem.cart_id == cart.id).delete(
                    synchronize_session=False
                )
                

            elif checkout.mode == "BUY_NOW":
                
                purchased_product_ids = [
                    item.product_id for item in checkout_items
                ]

                db.query(CartItem).filter(
                    CartItem.cart_id == cart.id,
                    CartItem.product_id.in_(purchased_product_ids),
                ).delete(synchronize_session=False)

        db.commit()

    except Exception:
        db.rollback()
        logger.exception("Order/payment flow failed", extra={"checkout_id": checkout_id, "user_id": current_user.id})
        raise
