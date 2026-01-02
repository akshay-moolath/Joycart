from fastapi import APIRouter, Depends,Request,Form, File, UploadFile,HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from app.db.db import get_db
from app.db.models import Seller,Product,OrderItems
from fastapi import BackgroundTasks
import cloudinary.uploader
from cloudinary.utils import cloudinary_url
import json,os
from collections import defaultdict
from app.auth import get_current_seller,get_current_user
from app.orders import restore_stock_for_item,refund_order_item
from app.db.models import User


router = APIRouter()

pages_router = APIRouter()

templates = Jinja2Templates(directory="templates")

cloudinary.config(
    cloud_name=os.getenv("CLOUD_NAME"),
    api_key=os.getenv("API_KEY"),
    api_secret=os.getenv("API_SECRET"),
    secure=True
)



####################Seller Register##################

@router.get("/seller/check")
def seller_check(request: Request,
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)):
    
    if current_user.is_seller:
        return RedirectResponse("/seller/dashboard", status_code=302)

    return RedirectResponse("/seller/registerform", status_code=302)
    
@router.post("/seller/register")
def register_seller(
    request: Request,
    background_tasks: BackgroundTasks,
    store_name: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
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

@pages_router.get("/seller/dashboard")
def seller_dashboard(request: Request,seller: Seller = Depends(get_current_seller)):
    return templates.TemplateResponse(
        "seller_dashboard.html",
        {"request": request
         }
    )

@pages_router.get("/seller/registerform")
def seller_register_page(request: Request):
    return templates.TemplateResponse(
        "seller_register.html",
        {"request": request}
    )



####################Product Create##################


@pages_router.get("/seller/product/add")
def seller_product_add(request: Request,seller: Seller = Depends(get_current_seller)):
    return templates.TemplateResponse(
        "seller_product_add.html",
        {"request": request}
    )

@router.post("/seller/product/create")
def create_product(
    request: Request,

    
    title: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    sku: str = Form(...),
    price: float = Form(...),
    discountPercentage: float = Form(0),
    stock: int = Form(...),
    availabilityStatus: str = Form(...),
    returnPolicy: str = Form(""),
    weight: int = Form(None),
    length: float = Form(None),
    width: float = Form(None),
    height: float = Form(None),
    shippingInformation: str = Form(""),
    warrantyInformation: str = Form(""),

    
    thumbnail: UploadFile = File(...),
    images: list[UploadFile] = File(...),

    db: Session = Depends(get_db),seller: Seller = Depends(get_current_seller)
):
    
    thumb_result = cloudinary.uploader.upload(
        thumbnail.file,
        folder=f"products/{seller.id}/thumbnail"
    )

    public_id = thumb_result["public_id"]
    thumbnail_url, _  = cloudinary_url(
    public_id,
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
            folder=f"products/{seller.id}/images"
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

   
    dimensions = None
    if length or width or height:
        dimensions = {
            "length": length,
            "width": width,
            "height": height
        }

   
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
        thumbnail=thumbnail_url,
        images=image_urls,
    )

    db.add(product)
    db.commit()

    return RedirectResponse("/seller/dashboard", status_code=302)


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

#######seller product page############

@pages_router.get("/seller/products")
def seller_products(
    request: Request,
    db: Session = Depends(get_db),seller: Seller = Depends(get_current_seller)
):

    products = (
        db.query(Product)
        .filter(Product.seller_id == seller.id)
        .order_by(Product.id.desc())
        .all()
    )

    return templates.TemplateResponse(
        "seller_products.html",
        {
            "request": request,
            "products": products
        }
    )

###############seller orders###############
@pages_router.get('/seller/orders')
def get_seller_order(request: Request,
    db: Session = Depends(get_db),seller: Seller = Depends(get_current_seller)):
    
    orderitems = (
    db.query(OrderItems, Product)
    .join(Product, Product.id == OrderItems.product_id)
    .filter(OrderItems.seller_id == seller.id)
    .order_by(OrderItems.id.desc())
    .all()
)


    grouped_orders = defaultdict(list)

    for item, product in orderitems:
        grouped_orders[item.order_id].append({
        "item": item,
        "product": product
    })

    return templates.TemplateResponse(
    "seller_orders.html",
    {
        "request": request,
        "grouped_orders": grouped_orders
    }
)

@router.post("/seller/order-item/{item_id}/action")
def seller_order_item_action(
    item_id: int,
    action: str = Form(...),
    seller: Seller = Depends(get_current_seller),
    db: Session = Depends(get_db)
):
    item = db.query(OrderItems).filter(
        OrderItems.id == item_id,
        OrderItems.seller_id == seller.id
    ).first()

    if not item:
        raise HTTPException(404, "Order item not found")

    valid_transitions = {
        "PLACED": ["ACCEPT", "CANCEL"],
        "ACCEPTED": ["SHIP", "CANCEL"],
        "SHIPPED": ["DELIVER"],
    }

    current_status = item.status
    action = action.upper()

    if current_status not in valid_transitions:
        raise HTTPException(400, "Action not allowed")

    if action not in valid_transitions[current_status]:
        raise HTTPException(400, "Invalid action for this status")

    
    if action == "ACCEPT":
        item.status = "ACCEPTED"
    elif action == "SHIP":
        item.status = "SHIPPED"
    elif action == "DELIVER":
        item.status = "DELIVERED"
    elif action == "CANCEL":
        if item.status in ["SHIPPED", "DELIVERED"]:
            raise HTTPException(400, "Cannot cancel shipped item")

        restore_stock_for_item(item, db)

        refund_order_item(item, db)
        
        item.status = "CANCELLED"

    db.commit()

    return RedirectResponse(
        "/seller/orders",
        status_code=302
    )