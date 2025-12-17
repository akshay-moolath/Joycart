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
        from_attributes = True

class LoginSchema(BaseModel):
    username: str
    password: str


class OrderCreate(BaseModel):
    amount:float


class OrderOut(BaseModel):
    id:int
    user_id:int
    amount:float
    status:str
    currency: str
    created_at:datetime

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int

class OrderItemOut(BaseModel):
    id: int
    order_id: int
    product_id: int
    quantity: int
    price_at_purchase: float

