#only used for first time to populate product table
import json
from app.db import SessionLocal
from app.models import Product

SELLER_ID = 1  # user1store

def populate_products():
    db = SessionLocal()

    with open("products.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    for item in data.get("products", []):

        product = Product(
            seller_id=SELLER_ID,

            title=item.get("title"),
            description=item.get("description"),
            category=item.get("category"),
            price=item.get("price"),
            discount_percentage=item.get("discountPercentage"),
            rating=item.get("rating"),
            stock=item.get("stock"),
            brand=item.get("brand"),
            sku=item.get("sku"),
            weight=item.get("weight"),

            warranty=item.get("warrantyInformation"),
            availability=item.get("availabilityStatus"),
            return_policy=item.get("returnPolicy"),

            thumbnail=item.get("thumbnail"),

            # store images list as JSON string
            images=json.dumps(item.get("images", []))
        )

        db.add(product)

    db.commit()
    db.close()

    print("✅ Products populated correctly")

if __name__ == "__main__":
    populate_products()
