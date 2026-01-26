from fastapi import APIRouter,Form,Depends
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from app.auth import get_current_user
from app.db.models import User,Review
from app.db.db import get_db
from app.reviews.services.reviews_service import add_review,load_reviews,rating_calculation


router = APIRouter()
pages_router = APIRouter()

templates = Jinja2Templates(directory="templates")



@router.post("/reviews/add")
def add_review_endpoint(
    product_id: int = Form(...),
    rating: int = Form(...),
    comment: str = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return add_review(product_id,rating,comment,current_user,db)


@router.get("/reviews/load")
def load_reviews_endpoint(
    product_id: int,
    db: Session = Depends(get_db)
):
    return load_reviews(product_id,db)


@router.get("/reviews/calculate")
def calculate_rating(
    product_id: int,
    db: Session = Depends(get_db)
):
    return rating_calculation(product_id,db)