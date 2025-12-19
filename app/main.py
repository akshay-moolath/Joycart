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

Base.metadata.create_all(bind = engine)

app = FastAPI()
app.mount('/static',  StaticFiles(directory='static'), name = 'static')
app.include_router(user_router, prefix="/api")
app.include_router(seller_router,prefix="/api")
app.include_router(cart_router,prefix="/api/cart")
app.include_router(viewcart_router,prefix='/api/cart')
app.include_router(product_page_router)


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
@app.get('/checkout')
def checkout():
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
@app.get("/favicon.ico")#added to remove favicon error
def favicon():
    return ""






