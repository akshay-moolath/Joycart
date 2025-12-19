#own
from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse,HTMLResponse
from fastapi.templating import Jinja2Templates
from app.auth import get_current_user
from app.db import Base, engine
from app.user import router as user_router
from app.seller import router as seller_router
from app.cart import router as cart_router
from app.viewcart import router as viewcart_router
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
app.include_router(product_page_router)
app.include_router(checkout_router,prefix="/api")
app.include_router(order_router,prefix="/api/orders")
app.include_router(payment_router,prefix="/api/payments")

templates = Jinja2Templates(directory="templates")


@app.get('/')
def home():
    return FileResponse("templates/homepage.html")
@app.get('/login')
def login():
    return FileResponse("templates/login.html")
@app.get("/register")
def register():
    return FileResponse("templates/register.html")
@app.get('/dashboard')
def dashboard():
    return FileResponse("templates/dashboard.html")
@app.get("/checkout/{order_id}")
def checkout_page(order_id: int):
    return FileResponse("templates/checkout.html")
@app.get('/hotdeals')
def hotdeals():
    return FileResponse("templates/hotdeals.html")
@app.get('/account')
def hotdeals():
    return FileResponse("templates/account.html")
@app.get('/cart')
def viewcart():   
    return FileResponse("templates/viewcart.html")
@app.get("/orders")
def orders_page():
    return FileResponse("templates/orders.html")
@app.get("/orders/{order_id}")
def order_detail_page():
    return FileResponse("templates/orderdetails.html")
@app.get("/favicon.ico")#added to remove favicon error
def favicon():
    return ""






