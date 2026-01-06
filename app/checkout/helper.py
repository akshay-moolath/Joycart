
from app.db.models import (
    Checkout, Payment, Order, OrderItems,
    Product, CheckoutItem, Cart, CartItem
)

def helper(current_user, db, checkout_id, method, razorpay_payment_id):
    try:
        checkout = db.query(Checkout).filter(
            Checkout.checkout_id == checkout_id
        ).first()

        if not checkout:
            raise Exception("Checkout not found")

        checkout_items = db.query(CheckoutItem).filter(
            CheckoutItem.checkout_id == checkout.id
        ).all()

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
                raise Exception(
                    f"Stock issue after payment for product {product.id}"
                )

            product.stock -= item.quantity

            order_items.append(
                OrderItems(
                    product_id=product.id,
                    quantity=item.quantity,
                    seller_id=product.seller_id,
                    price_at_purchase=item.price_at_checkout,
                    status="PLACED"
                )
            )

        
        order = Order(
            user_id=current_user.id,
            amount=checkout.amount,
            checkout_id=checkout.checkout_id,
            shipping_address=checkout.shipping_address,
            status="PLACED",
            currency="INR"
        )

        db.add(order)
        db.flush()

        for oi in order_items:
            oi.order_id = order.id

        
        if method == "COD":
            payment = Payment(
                order_id=order.id,
                amount=order.amount,
                status="PENDING",
                method="COD"
            )
        else:
            payment = Payment(
                order_id=order.id,
                amount=order.amount,
                status="SUCCESS",
                method=method.upper(),
                gateway_payment_id=razorpay_payment_id
            )

        checkout.status = "COMPLETED"

        db.add_all(order_items)
        db.add(payment)

        
        db.query(CheckoutItem).filter(
            CheckoutItem.checkout_id == checkout.id
        ).delete(synchronize_session=False)

        db.delete(checkout)

        if checkout.mode == "CART":
            cart = db.query(Cart).filter(
                Cart.user_id == current_user.id
            ).first()
            if cart:
                db.query(CartItem).filter(
                    CartItem.cart_id == cart.id
                ).delete(synchronize_session=False)

        db.commit()

    except Exception as e:
        db.rollback()
        print("❌ ORDER / PAYMENT FAILED:", str(e))
        raise
