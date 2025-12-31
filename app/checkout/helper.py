from fastapi import HTTPException
from app.db.models import Cart,CartItem,Checkout,Payment,Order,OrderItems,Product,CheckoutItem
from sqlalchemy.orm import Session


def helper(current_user,db,checkout_id,method,gateway_payment_id):

    if method == "COD":
           order_status = "PLACED"
           payment_status = "DUE"
    else:
           order_status = payment_status = "PAID"

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
            raise HTTPException(409, "Order already processed")

    checkout_items = db.query(CheckoutItem).filter(
        CheckoutItem.checkout_id == checkout.id
    ).all()

    if not checkout_items:
        raise HTTPException(400, "No checkout items")

    total_amount = 0
    order_items = []
        
    product_ids = [item.product_id for item in checkout_items]
    products = (
            db.query(Product)
            .filter(Product.id.in_(product_ids))
            .with_for_update()
            .all()
        )
    product_map = {p.id: p for p in products}

    for item in checkout_items:
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
            status=order_status,
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
                status=payment_status,
                method= method
        )
    else:
        payment = Payment(
                order_id=order.id,
                amount=order.amount,
                status=payment_status,
                method= method,
                gateway_payment_id = gateway_payment_id
        )

    db.add_all(order_items)
    db.add(payment)

        
    db.query(CheckoutItem).filter(
        CheckoutItem.checkout_id == checkout.id
    ).delete()

    db.delete(checkout)
    db.commit()

    return order


