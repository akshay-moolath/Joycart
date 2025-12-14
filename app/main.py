#own
from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.auth import get_current_user
from app.db import Base, engine
from app.user import router as user_router

Base.metadata.create_all(bind = engine)

app = FastAPI()
app.mount('/static',  StaticFiles(directory='static'), name = 'static')
app.include_router(user_router, prefix="/api")


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
@app.get('/product')
def product():
    return FileResponse("templates/product.html")
@app.get('/hotdeals')
def hotdeals():
    return FileResponse("templates/hotdeals.html")
@app.get('/account')
def hotdeals():
    return FileResponse("templates/account.html")

@app.get("/favicon.ico")#added to remove favicon error
def favicon():
    return ""