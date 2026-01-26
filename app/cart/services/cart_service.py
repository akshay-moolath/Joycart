from app.db.models import Product,Cart,CartItem
from fastapi import HTTPException

def add_to_carts(product_id,quantity,current_user,db):

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

def get_carts(current_user,db):

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

def update_quantity(item_id,quantity,current_user,db):

    item = (db.query(CartItem).join(Cart).filter(CartItem.id == item_id,Cart.user_id == current_user.id).first())
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    item.quantity = quantity
    db.commit()

    return {"message": "Quantity updated"}

def delete_quantity(item_id,current_user,db):

    item = (db.query(CartItem).join(Cart).filter(CartItem.id == item_id,Cart.user_id == current_user.id).first())
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()

    return {"message": "Item removed"}

def cart_count(current_user,db):
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

def is_in_cart(product_id,current_user,db):
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

