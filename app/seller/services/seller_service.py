from app.db.models import Seller,Product,Payment,Order,OrderItems
from sqlalchemy.orm import Session
import json
from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from app.orders.services.orders_service import restore_stock_for_item,initiate_razorpay_refund,create_refund_record

def register_seller(background_tasks,store_name,current_user,db):
    seller = Seller(
        user_id=current_user.id,
        store_name=store_name
    )
    current_user.is_seller = True

    db.add(seller)
    db.commit()
    db.refresh(seller)

    current_user.seller_id = seller.id

    if seller.id == 1 or seller.id == 2:
        
        background_tasks.add_task(populate_products, db, seller.id)
    
    return seller

def populate_products(db: Session, seller_id: int):

    if seller_id ==1:
        file = "products1.json"
    else:
        file = "products2.json"

    with open(file, "r", encoding="utf-8") as f:
        data = json.load(f)

    for item in data.get("products", []):
        product = Product(
            seller_id=seller_id,

            title=item.get("title"),
            description=item.get("description"),
            category=item.get("category"),
            price=item.get("price"),
            discountPercentage=item.get("discountPercentage"),
            rating=item.get("rating"),
            stock=item.get("stock"),
            brand=item.get("brand"),
            sku=item.get("sku"),
            dimensions=item.get("dimensions"),
            weight=item.get("weight"),
            warrantyInformation=item.get("warrantyInformation"),
            availabilityStatus=item.get("availabilityStatus"),
            shippingInformation=item.get("shippingInformation"),
            returnPolicy=item.get("returnPolicy"),
            thumbnail=item.get("thumbnail"),
            images=item.get("images"),
        )

        db.add(product)

    db.commit()

def create_product(title,description,category,sku,price,discountPercentage,stock,availabilityStatus,returnPolicy,weight,
    length,width,height,shippingInformation,warrantyInformation,thumbnail,images,db,seller):

    existing = db.query(Product).filter(
        Product.sku == sku,
        Product.seller_id == seller.id
    ).first()
    if existing:
        raise HTTPException(400, "SKU already exists")

    dimensions = (
        {"length": length, "width": width, "height": height}
        if any(v is not None for v in (length, width, height))
        else None
    )

    product = Product(
        seller_id=seller.id,
        title=title,
        description=description,
        category=category,
        sku=sku,
        price=price,
        discountPercentage=discountPercentage,
        stock=stock,
        availabilityStatus=availabilityStatus,
        returnPolicy=returnPolicy,
        weight=weight,
        dimensions=dimensions,
        shippingInformation=shippingInformation,
        warrantyInformation=warrantyInformation,
        thumbnail=thumbnail,
        images=json.loads(images),
    )

    db.add(product)
    db.commit()

def edit_product(product_id,title,description,category,sku,price,discountPercentage,stock,availabilityStatus,
    returnPolicy,weight,length,width,height,shippingInformation,warrantyInformation,thumbnail,images,db,seller):

    product = db.query(Product).filter(
        Product.id == product_id,
        Product.seller_id == seller.id
    ).first()

    if not product:
        raise HTTPException(404, "Product not found")

    
    if thumbnail:
        product.thumbnail = thumbnail

    if images:
        product.images = json.loads(images)

    product.title = title
    product.description = description
    product.category = category
    product.sku = sku
    product.price = price
    product.discountPercentage = discountPercentage
    product.stock = stock
    product.availabilityStatus = availabilityStatus
    product.returnPolicy = returnPolicy
    product.weight = weight
    product.shippingInformation = shippingInformation
    product.warrantyInformation = warrantyInformation

    product.dimensions = (
        {"length": length, "width": width, "height": height}
        if any(v is not None for v in (length, width, height))
        else None
    )

    db.commit()

def delete_product(product_id, current_seller, db):

    product = (
        db.query(Product)
        .filter(
            Product.id == product_id,
            Product.seller_id == current_seller.id
        )
        .first()
    )

    if not product:
        raise HTTPException(404, "Product not found")

    active_order_exists = (
        db.query(OrderItems)
        .filter(
            OrderItems.product_id == product.id,
            OrderItems.seller_id == current_seller.id,
            OrderItems.status != "CANCELLED"
        )
        .first()
    )

    if active_order_exists:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete product with active orders"
        )

    db.delete(product)
    db.commit()

    return {"message": "Product deleted successfully"}

def seller_orders(db,seller):

    orderitems = (
    db.query(OrderItems, Product, Order)
    .join(Product, Product.id == OrderItems.product_id)
    .join(Order, Order.id == OrderItems.order_id)
    .filter(OrderItems.seller_id == seller.id)
    .order_by(OrderItems.id.desc())
    .all()
)
    order_ids = {order.id for _, _, order in orderitems}

    payments = (
    db.query(Payment)
    .filter(Payment.order_id.in_(order_ids))
    .order_by(Payment.created_at.desc())
    .all()
)
    payment_map = {}

    for payment in payments:
        if payment.order_id not in payment_map:
            payment_map[payment.order_id] = payment


    grouped_orders = {}

    for item, product, order in orderitems:

        if order.id not in grouped_orders:
            payment = payment_map.get(order.id)

            grouped_orders[order.id] = {
                "payment_status": payment.status  if payment else "N/A",
                "items": []
            }

        grouped_orders[order.id]["items"].append({
            "item": item,
            "product": product
        })

    return grouped_orders

def order_item_action(item_id,action,seller,db):
    refund = None 
    

    try:
        item = (
            db.query(OrderItems)
            .join(Order)
            .filter(
                OrderItems.id == item_id,
                OrderItems.seller_id == seller.id
            )
            .first()
        )

        if not item:
            raise HTTPException(404, "Order item not found")

        if item.status == "CANCELLED":
            return RedirectResponse("/seller/orders", status_code=302)

        valid_transitions = {
            "PLACED": ["CONFIRM", "CANCEL"],
            "CONFIRMED": ["SHIP", "CANCEL"],
            "SHIPPED": ["DELIVER"],
        }

        action = action.upper()

        if item.status not in valid_transitions:
            raise HTTPException(400, "Action not allowed")

        if action not in valid_transitions[item.status]:
            raise HTTPException(400, "Invalid action for this status")

        if action == "CONFIRM":
            item.status = "CONFIRMED"

        elif action == "SHIP":
            item.status = "SHIPPED"

        elif action == "DELIVER":
            item.status = "DELIVERED"

        elif action == "CANCEL":
            if item.status in ["SHIPPED", "DELIVERED"]:
                raise HTTPException(400, "Cannot cancel shipped item")
            
            payment = (
                        db.query(Payment)
                        .filter(Payment.order_id == item.order_id)
                        .first()
                    )
            
            restore_stock_for_item(item, db)
            item.status = "CANCELLED"
            if payment and payment.method == "COD":
                payment.status = "NOT_REQUIRED"
            elif payment:
                refund = create_refund_record(item, payment, db)

        db.commit()  

        if refund:
            initiate_razorpay_refund(refund)  

        return RedirectResponse("/seller/orders", status_code=302)

    except Exception as e:  
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database / gateway error: {str(e)}"
        )