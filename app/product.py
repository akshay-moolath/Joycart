from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from app.db import get_db
from app.models import Product
from app.schemas import ProductOut

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_model=list[ProductOut]) #for swagger
def get_products(db: Session = Depends(get_db)):
    return db.query(Product).all()



def list_products(db: Session = Depends(get_db)):
    return db.query(Product).order_by(Product.id.desc()).all()
    
@router.get("/{product_id}", response_model=ProductOut)#for swagger
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


