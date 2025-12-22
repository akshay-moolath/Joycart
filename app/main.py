#own
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse,RedirectResponse
from fastapi.templating import Jinja2Templates
from app.auth import get_current_user
from app.db import Base, engine
from app.user import router as user_router
from app.seller import router as seller_router
from app.cart import router as cart_router
from app.viewcart import router as viewcart_router
from app.product import router as product_router
from app.product_page import router as product_page_router
from app.checkout import router as checkout_router
from app.orders import router as order_router
from app.payments import router as payment_router

Base.metadata.create_all(bind = engine)

app = FastAPI()
app.mount('/static',  StaticFiles(directory='static'), name = 'static')
app.include_router(user_router, prefix="/api")
app.include_router(seller_router,prefix="/api")
app.include_router(cart_router,prefix="/api/cart")
app.include_router(viewcart_router,prefix='/api/cart')
app.include_router(product_router,prefix='/api/products')
app.include_router(product_page_router)
app.include_router(checkout_router,prefix="/api")
app.include_router(order_router,prefix="/api/orders")
app.include_router(payment_router,prefix="/api/payments")

templates = Jinja2Templates(directory="templates")


@app.get("/")
def homepage(request: Request):
    token = request.cookies.get("access_token")

    if token:
        return RedirectResponse(url="/dashboard", status_code=302)

    return templates.TemplateResponse(
        "homepage.html",
        {"request": request}
    )
@app.get('/login')
def login(request: Request):
    token = request.cookies.get("access_token")

    if token:
        return RedirectResponse("/dashboard", status_code=302)

    return templates.TemplateResponse(
        "login.html",
        {"request": request}
    )
@app.get("/register")
def register(request: Request):
     return templates.TemplateResponse(
        "register.html",
        {"request": request}
    )
@app.get("/dashboard")
def dashboard(request: Request):
    return templates.TemplateResponse(
        "dashboard.html",
        {"request":request}
    )
@app.get("/checkout/{order_id}")
def checkout_page(request: Request):
    return templates.TemplateResponse(
        "checkout.html",
        {"request":request}
    )
@app.get('/cart')
def viewcart(request: Request):   
    return templates.TemplateResponse(
        "viewcart.html",
        {"request":request}
    )
def orders_page(request: Request):
        return templates.TemplateResponse(
        "orders.html",
        {"request":request}
    )
@app.get("/orders/{order_id}")
def order_detail_page(request: Request):
        return templates.TemplateResponse(
        "orderdetails.html",
        {"request":request}
    )
@app.get("/payment-success/{order_id}")
def payment_success(request: Request):
        return templates.TemplateResponse(
        "payment_success.html",
        {"request":request}
    )
@app.get("/favicon.ico")#added to remove favicon error
def favicon():
    return ""






