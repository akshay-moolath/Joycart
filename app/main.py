#own
from fastapi import FastAPI, Request, Depends,HTTPException
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from app.auth import get_current_user
from app.db.db import Base, engine,get_db
from app.product import list_products
from app.user import router as user_router
from app.user import pages_router as user_pages_router
from app.seller import router as seller_router
from app.seller import pages_router as seller_pages_router
from app.cart import router as cart_router
from app.cart import pages_router as cart_pages_router
from app.product import router as product_router
from app.checkout.checkout import router as checkout_router
from app.checkout.checkout import pages_router as checkout_pages_router
from app.checkout.checkout import razorpay_router as checkout_razorpay_router
from app.checkout.cod import router as cod_router
from app.checkout.cod import pages_router as cod_pages_router
from app.orders import router as order_router
from app.orders import pages_router as order_pages_router
from app.reviews import router as review_router
from app.reviews import pages_router as review_pages_router


Base.metadata.create_all(bind = engine)


app = FastAPI()

app.mount('/static',  StaticFiles(directory='static'), name = 'static')

app.include_router(user_router, prefix="/api")
app.include_router(user_pages_router)
app.include_router(seller_router,dependencies=[Depends(get_current_user)])
app.include_router(seller_pages_router,dependencies=[Depends(get_current_user)])
app.include_router(cart_router,prefix="/api/cart",dependencies=[Depends(get_current_user)])
app.include_router(cart_pages_router,dependencies=[Depends(get_current_user)])
app.include_router(product_router)
app.include_router(checkout_router,prefix="/api",dependencies=[Depends(get_current_user)])
app.include_router(checkout_pages_router,dependencies=[Depends(get_current_user)])
app.include_router(checkout_razorpay_router)
app.include_router(cod_router,prefix="/api",dependencies=[Depends(get_current_user)])
app.include_router(cod_pages_router,dependencies=[Depends(get_current_user)])
app.include_router(order_router,prefix="/api/orders",dependencies=[Depends(get_current_user)])
app.include_router(order_pages_router, dependencies=[Depends(get_current_user)])
app.include_router(review_router,prefix ="/api",dependencies=[Depends(get_current_user)])
app.include_router(review_pages_router,dependencies=[Depends(get_current_user)])




templates = Jinja2Templates(directory="templates")

@app.get("/")
def joycart(
    request: Request,
    db: Session = Depends(get_db)
):
    token = request.cookies.get("access_token")

    if token:
        return RedirectResponse("/home")

    products = list_products(db)

    return templates.TemplateResponse(
        "joycart.html",
        {"request": request, "products": products}
    )
    
@app.get("/favicon.ico")#added to remove favicon error
def favicon():
    return ""






