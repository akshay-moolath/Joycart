from fastapi import APIRouter, Depends,Request,Form, File, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from app.db import get_db
from app.models import Seller
from app.models import Product
from fastapi import BackgroundTasks
import cloudinary.uploader
from cloudinary.utils import cloudinary_url
import json


router = APIRouter()

templates = Jinja2Templates(directory="templates")


############################################seller register endpoints######################################

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
def seller_dashboard(request: Request):
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

################################# Product Creation endpoints ################################################

@router.post("/seller/product/create")
def create_product(
    request: Request,
    background_tasks: BackgroundTasks,

    title: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    sku: str = Form(...),
    price: float = Form(...),
    stock: int = Form(...),

    thumbnail: UploadFile = File(...),
    images: list[UploadFile] = File(...),

    db: Session = Depends(get_db)
):
    current_user = request.state.user
    seller = db.query(Seller).filter(Seller.user_id == current_user.id).first()

    
    product = Product(
        seller_id=seller.id,
        title=title,
        description=description,
        category=category,
        sku=sku,
        price=price,
        stock=stock,
        thumbnail=None,
        images=[]
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    
    background_tasks.add_task(
        upload_product_images,
        product.id,
        seller.id,
        thumbnail,
        images,
        db
    )

    
    return RedirectResponse("/seller/dashboard", status_code=302)

@router.get("/seller/product/form")
def seller_register_page(request: Request):
    return templates.TemplateResponse(
        "seller_product_form.html",
        {"request": request}
    )

def upload_product_images(
    product_id: int,
    seller_id: int,
    thumbnail: UploadFile,
    images: list[UploadFile],
    db:Session
):
    

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return

    
    thumb_result = cloudinary.uploader.upload(
        thumbnail.file,
        folder=f"products/{seller_id}/thumbnail"
    )
    thumb_public_id = thumb_result["public_id"]

    thumbnail_url, _ = cloudinary_url(
        thumb_public_id,
        width=300,
        height=300,
        crop="fill",
        gravity="auto",
        fetch_format="auto",
        quality="auto"
    )

    
    image_urls = []
    for img in images:
        result = cloudinary.uploader.upload(
            img.file,
            folder=f"products/{seller_id}/images"
        )

        public_id = result["public_id"]
        url, _ = cloudinary_url(
            public_id,
            width=1000,
            height=1000,
            crop="fill",
            gravity="auto",
            fetch_format="auto",
            quality="auto"
        )
        image_urls.append(url)

    product.thumbnail = thumbnail_url
    product.images = image_urls
    db.commit()
    db.close()

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

