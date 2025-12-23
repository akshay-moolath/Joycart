from fastapi import APIRouter, Depends,Request,Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from app.db import get_db
from app.models import Seller
from app.models import Product
from fastapi import BackgroundTasks
import json

router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.get("/seller/check")
def seller_check(request: Request, db: Session = Depends(get_db)):
    current_user = request.state.user
    if current_user.is_seller:
        return RedirectResponse("/seller/dashboard", status_code=302)

    return RedirectResponse("/seller/registerform", status_code=302)
    
@router.post("/seller/register")
def register_seller(
    request: Request,
    background_tasks: BackgroundTasks,
    store_name: str = Form(...),
    db: Session = Depends(get_db)
):
    current_user = request.state.user

    seller = Seller(
        user_id=current_user.id,
        store_name=store_name
    )
    current_user.is_seller = True

    db.add(seller)
    db.commit()
    db.refresh(seller)

    if current_user.id == 1:
        background_tasks.add_task(populate_products, db, seller.id)

    return RedirectResponse("/seller/dashboard", status_code=302)

@router.get("/seller/dashboard")
def seller_dashboard(request: Request,db: Session = Depends(get_db)):


    return templates.TemplateResponse(
        "seller_dashboard.html",
        {"request": request
         }
    )

@router.get("/seller/registerform")
def seller_register_page(request: Request):
    return templates.TemplateResponse(
        "seller_register.html",
        {"request": request}
    )

def populate_products(db: Session, seller_id: int):
    with open("products.json", "r", encoding="utf-8") as f:
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

