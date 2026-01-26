from fastapi import APIRouter, Depends,Request,Form,HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from app.db.db import get_db
from app.db.models import Seller,Product
from fastapi import BackgroundTasks
from decimal import Decimal
from app.auth import get_current_seller,get_current_user
from app.db.models import User
from app.seller.services.seller_service import register_seller,create_product,edit_product,delete_product,seller_orders,order_item_action


router = APIRouter()

pages_router = APIRouter()

templates = Jinja2Templates(directory="templates")


####################Seller Register##################

@router.get("/seller/check")
def seller_check(request: Request,
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)):
    
    if current_user.is_seller:
        return RedirectResponse("/seller/dashboard", status_code=302)

    return RedirectResponse("/seller/registerform", status_code=302)
    
@router.post("/seller/register")
def register_seller_endpoint(
    background_tasks: BackgroundTasks,
    store_name: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    register_seller(background_tasks,store_name,current_user,db)

    return RedirectResponse("/seller/dashboard", status_code=302)

@pages_router.get("/seller/dashboard")
def seller_dashboard(request: Request,
        seller: Seller = Depends(get_current_seller),
        db: Session = Depends(get_db)):
    
    seller = db.query(Seller).filter(Seller.id == seller.id).first()
    return templates.TemplateResponse(
        "seller_dashboard.html",
        {"request": request,
         "store_name":seller.store_name.upper()
         }
    )

@pages_router.get("/seller/registerform")
def seller_register_page(request: Request,
        current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse(
        "seller_register.html",
        {"request": request,
         "current_user":current_user}
    )



####################Product Create##################


@pages_router.get("/seller/product/add")
def seller_product_add(request: Request,seller: Seller = Depends(get_current_seller)):
    return templates.TemplateResponse(
        "seller_product_add.html",
        {"request": request}
    )


@router.post("/seller/product/create")
def create_product_endpoint(
    title: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    sku: str = Form(...),
    price: Decimal = Form(...),
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

    thumbnail: str = Form(...),
    images: str = Form("[]"),

    db: Session = Depends(get_db),
    seller: Seller = Depends(get_current_seller)
):
    create_product(title,description,category,sku,price,discountPercentage,stock,availabilityStatus,returnPolicy,weight,
    length,width,height,shippingInformation,warrantyInformation,thumbnail,images,db,seller)

    return RedirectResponse("/seller/dashboard", status_code=302)


@pages_router.get("/seller/products/edit/{product_id}")
def edit_product_page(
    request: Request,
    product_id: int,
    current_seller = Depends(get_current_seller),
    db: Session = Depends(get_db)):

    product = db.query(Product).filter(
        Product.id == product_id,
        Product.seller_id == current_seller.id
    ).first()

    if not product:
        raise HTTPException(status_code=404,detail="Product not found")


    return templates.TemplateResponse(
        "seller_product_edit.html",{
            "request":request,
            "product":product}
    )


@router.post("/seller/products/editfn/{product_id}")
def edit_product_endpoint(
    product_id: int,

    title: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    sku: str = Form(...),
    price: Decimal = Form(...),
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

    
    thumbnail: str = Form(None),
    images: str = Form(None),

    db: Session = Depends(get_db),
    seller: Seller = Depends(get_current_seller)
):
    edit_product(product_id,title,description,category,sku,price,discountPercentage,stock,availabilityStatus,
    returnPolicy,weight,length,width,height,shippingInformation,warrantyInformation,thumbnail,images,db,seller)

    return RedirectResponse("/seller/products", status_code=302)


@router.post("/seller/products/delete/{product_id}")
def delete_product_endpoint(
    product_id: int,
    current_seller = Depends(get_current_seller),
    db: Session = Depends(get_db)):
    
    delete_product(product_id,current_seller,db)
    return RedirectResponse("/seller/products", status_code=302)



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
    
    grouped_orders = seller_orders(db,seller)

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
    return order_item_action(item_id,action,seller,db)
