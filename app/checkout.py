from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.db import get_db
from app.models import Cart, Product, Order, OrderItems

router = APIRouter()
pages_router = APIRouter()

templates = Jinja2Templates(directory="templates")

@pages_router.get("/checkout/{order_id}")
def checkout_page(request: Request):
    return templates.TemplateResponse(
        "checkout.html",
        {"request":request}
    )