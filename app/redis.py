import redis, os, json
from sqlalchemy.orm import Session
from app.db.models import Product
from app.product import list_products

REDIS_URL = os.getenv("REDIS_URL")
CACHE_KEY = os.getenv("CACHE_KEY")

redis_client = redis.Redis.from_url(
    REDIS_URL,
    decode_responses=True
)

def set_cache(key: str, value, ttl: int = 60):
    redis_client.setex(key, ttl, json.dumps(value))

def get_cache(key: str):
    data = redis_client.get(key)
    if data:
        return json.loads(data)
    return None


def product_to_dict(product):
    return {
        "id": product.id,
        "title": product.title,
        "price": float(product.price),
        "thumbnail": product.thumbnail,
        "discountPercentage":product.discountPercentage,
        "seller_id": product.seller_id
    }


def get_all_products_cached(db: Session):
    cached_products = get_cache(CACHE_KEY)

    if cached_products:
        print("Loaded products from REDIS")
        return cached_products

    print(" Loaded products from DB")
    products = list_products(db)
    products_data = [product_to_dict(p) for p in products]

    set_cache(CACHE_KEY, products_data, ttl=120)
    return products_data
