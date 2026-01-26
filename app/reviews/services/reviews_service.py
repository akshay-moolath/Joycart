from app.db.models import Review, Order,OrderItems,User, Product
from fastapi import HTTPException
from sqlalchemy import func

def add_review(product_id,rating,comment,current_user,db):

    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(404, "Product not found")

    if rating < 1 or rating > 5:
        raise HTTPException(400, "Rating must be between 1 and 5")

    
    has_bought = db.query(OrderItems).join(
        Order, Order.id == OrderItems.order_id
    ).filter(
        Order.user_id == current_user.id, 
        OrderItems.product_id == product_id,
        OrderItems.status == "DELIVERED"
    ).first() is not None

    if not has_bought:
        raise HTTPException(
            403,
            "Only people who bought this product can add a review"
        )

    
    existing_review = db.query(Review).filter(
        Review.product_id == product_id,
        Review.user_id == current_user.id
    ).first()

    if existing_review:
        raise HTTPException(400, "You already reviewed this product")

    review = Review(
        product_id=product_id,
        user_id=current_user.id,
        rating=rating,
        comment=comment
    )

    db.add(review)
    db.commit()

    return {"message": "Review added"}

def load_reviews(product_id,db):

    reviews = (
        db.query(Review, User.username)
        .join(User, User.id == Review.user_id)
        .filter(Review.product_id == product_id)
        .order_by(Review.created_at.desc())
        .all()
    )
    return [
        {
            "username": username,
            "rating": review.rating,
            "comment": review.comment,
            "created_at": review.created_at.isoformat()

        }
        for review, username in reviews
    ]

def rating_calculation(product_id,db):
    
    reviews = db.query(Review).filter(
        Review.product_id == product_id
    ).all()

    if not reviews:
        return {
            "average_rating": 0,
            "total_reviews": 0
        }

    avg, count = db.query(
        func.avg(Review.rating),
        func.count(Review.id)
    ).filter(
        Review.product_id == product_id
    ).first()

    return {
        "average_rating": avg,
        "total_reviews": count
    }