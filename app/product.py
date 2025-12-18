from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json

from app.db import get_db
from app.models import Product
from app.schemas import ProductOut

router = APIRouter()

@router.get("/", response_model=list[ProductOut]) #######get all products#######
def get_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return products

@router.get("/{product_id}", response_model=ProductOut)  #######get single product#######
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
