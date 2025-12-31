from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float,Boolean,JSON,Numeric
from app.db.db import Base
from sqlalchemy.orm import relationship
from datetime import datetime,timedelta


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False) 
    is_seller = Column(Boolean, default=False)

class Address(Base):
    __tablename__ = "addresses"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    name = Column(String, nullable=False)          # Receiver name
    phone = Column(String, nullable=False)

    address_line1 = Column(String, nullable=False)
    address_line2 = Column(String, nullable=True)

    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    pincode = Column(String, nullable=False)

    is_default = Column(Boolean, default=False)

    user = relationship("User", backref="addresses")

class Seller(Base):
    __tablename__ = "sellers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    store_name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User")


class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    seller_id = Column(Integer, ForeignKey("sellers.id"), nullable=False)
    title = Column(String)
    description = Column(String)
    category = Column(String)
    price = Column(Float)
    discountPercentage = Column(Float)
    rating = Column(Float)
    stock = Column(Integer)
    brand = Column(String,nullable=True)
    sku = Column(String)
    weight = Column(Integer)
    dimensions = Column(JSON, nullable=True)
    warrantyInformation = Column(String)
    shippingInformation = Column(String)
    availabilityStatus = Column(String)
    returnPolicy = Column(String)
    thumbnail = Column(String)
    images = Column(JSON, nullable=False) 
    reviews = relationship("Review", back_populates="product")

class Checkout(Base):
    __tablename__ = "checkouts"

    id = Column(Integer, primary_key=True)
    checkout_id = Column(String, unique=True, nullable=False, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    mode = Column(String) 

    shipping_address = Column(JSON, nullable=True)

    amount = Column(Integer, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(
        DateTime,
        default=lambda: datetime.utcnow() + timedelta(minutes=30)
    )   

class CheckoutItem(Base):
    __tablename__ = "checkout_items"

    id = Column(Integer, primary_key=True, index=True)

    checkout_id = Column(
        ForeignKey("checkouts.id", ondelete="CASCADE"),
        nullable=False
    )

    product_id = Column(
        ForeignKey("products.id"),
        nullable=False
    )

    quantity = Column(Integer, nullable=False)
    price_at_checkout = Column(Numeric(10, 2), nullable=False)
     
    product = relationship("Product")
 

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    checkout_id = Column(String, unique=True, nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String, nullable=False)
    currency = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    shipping_address = Column(JSON,nullable=True)


class OrderItems(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    seller_id = Column(Integer, ForeignKey("sellers.id"),nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price_at_purchase = Column(Float, nullable=False)
    status = Column(String, default="PLACED",nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class Cart(Base):
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    items = relationship("CartItem",back_populates="cart",cascade="all, delete-orphan")

class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)
    cart_id = Column(Integer, ForeignKey("carts.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)

    cart = relationship("Cart", back_populates="items")
                        
    
class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String, nullable=False) # success | failed
    method = Column(String, nullable=False)
    gateway_payment_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)



class Review(Base):
    __tablename__ = 'reviews'

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id')) # The Link
    rating = Column(Float)
    comment = Column(String)
    date = Column(DateTime, default=datetime.utcnow, nullable=False)

    reviewerName = Column(String)
    product = relationship("Product", back_populates="reviews")





