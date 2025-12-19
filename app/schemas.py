from pydantic import BaseModel, Field, constr
from typing import Optional
from datetime import datetime


#user create schema 
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    
#user info schema
class UserOut(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        orm_attributes = True

class SellerCreate(BaseModel):
    store_name: str

class SellerOut(BaseModel):
    id: int
    store_name: str
    is_active: bool

    class Config:
        orm_attributes = True

class LoginSchema(BaseModel):
    username: str
    password: str

class ProductCreate(BaseModel): 
    title : str
    description : str
    category : str
    price : float
    discountPercentage : float
    stock :int
    brand : Optional[str] = None
    weight : int
    warranty : str
    availability : str
    return_policy : str
    thumbnail : str
    images : list[str]

class DimensionSchema(BaseModel):
    width: float
    height: float
    depth: float

class ProductOut(BaseModel):

    id : int
    title : str
    description : str
    category : str
    price : float
    discountPercentage : float
    rating : float
    stock :int
    brand : Optional[str] = None
    sku : str
    weight : int
    dimensions : DimensionSchema
    warrantyInformation : str
    shippingInformation : str
    availabilityStatus : str
    returnPolicy : str
    thumbnail : str
    images : list[str] 


class CartAdd(BaseModel):
    product_id: int
    quantity: int = 1

class CartItem(BaseModel):
    id:int
    cart_id:int
    product_id:int
    quantity:int

class CartItemOut(BaseModel):
    product_id: int
    quantity: int

    class Config:
        orm_attributes = True
class CartOut(BaseModel):
    id: int
    items: list[CartItemOut]

    class Config:
        orm_attributes = True



class OrderCreate(BaseModel):
    amount:float


class OrderOut(BaseModel):
    id:int
    user_id:int
    amount:float
    status:str
    currency: str
    created_at:datetime
    expires_at: datetime 
    class Config:
        orm_attributes = True

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int

class OrderItemOut(BaseModel):
    id: int
    order_id: int
    product_id: int
    quantity: int
    price_at_purchase: float

class PaymentOut(BaseModel):
    id: int
    order_id: int
    status: str
    gateway: str
    gateway_payment_id:str
    created_at:datetime
    class Config:
        orm_attributes = True

class ReviewCreate(BaseModel):
    rating:float
    comment:str

class ReviewOut(BaseModel):
    id:int
    product_id:int
    rating:float
    comment:str
    date:datetime
    reviewerName:str
