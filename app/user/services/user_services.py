from app.db.models import User, Seller, Address
from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from app.auth import hash_password,verify_password,create_access_token
from app.redis import get_all_products_cached


def create_user(username,email,password,db):
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="username already exists")
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="email already exists")

    user = User(
        username=username,
        email=email,
        password=hash_password(password)
    )
     
    db.add(user)
    db.commit()
    db.refresh(user)

    if user.id == 1:
        user.role = "admin"

    db.commit()

    return user

def authenticate_user(username: str, password: str, db):
    
    user = db.query(User).filter(
        User.username == username
    ).first()

    if not user or not verify_password(password, user.password):
        return None

    return user

def home(current_user,db):
    products = get_all_products_cached(db)  #use (products = list_products(db)) in case of db

    if current_user.is_seller:
        seller = (
            db.query(Seller)
            .filter(Seller.user_id == current_user.id)
            .first()
        )

        if seller:
            products = [
                p for p in products
                if p["seller_id"] != seller.id    # use (if p.seller_id != seller.id) in case of db .
            ]
    return products

def profile(section,edit,current_user,db):

    addresses = []
    address_to_edit = None

    if section == "address":
        addresses = (
            db.query(Address)
            .filter(Address.user_id == current_user.id)
            .all()
        )

        if edit:
            address_to_edit = (
                db.query(Address)
                .filter(
                    Address.id == edit,
                    Address.user_id == current_user.id
                )
                .first()
            )
    return (addresses,address_to_edit)

def update_profile(username,email,current_user,db):

    user = db.query(User).filter(User.id == current_user.id).first()

    
    if username and username != user.username:
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already taken")
        user.username = username

    
    if email and email != user.email:
        existing_email = db.query(User).filter(User.email == email).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already in use")
        user.email = email

    db.commit()

    return user

def add_address(current_user,name,phone,address_line1,address_line2,city,state,pincode,is_default,db):
    if is_default:
        db.query(Address).filter(
            Address.user_id == current_user.id,
            Address.is_default == True
        ).update({"is_default": False})

    address = Address(
        user_id=current_user.id,
        name=name,
        phone=phone,
        address_line1=address_line1,
        address_line2=address_line2,
        city=city,
        state=state,
        pincode=pincode,
        is_default=is_default
    )

    db.add(address)
    db.commit()

    return address

def edit_address(address_id,name,phone,city,state,address_line1,address_line2,pincode,current_user,db):

    address = db.query(Address).filter(
        Address.id == address_id,
        Address.user_id == current_user.id
    ).first()

    if not address:
        raise HTTPException(status_code=404, detail="Address not found")

    address.name = name
    address.city = city
    address.phone = phone
    address.address_line1 = address_line1
    address.address_line2 = address_line2
    address.city = city
    address.state = state
    address.pincode = pincode
    
    db.commit()

    return address

def delete_address(address_id,current_user,db):
    address_count = db.query(Address).filter(
        Address.user_id == current_user.id
    ).count()

    if address_count <= 1:
        raise HTTPException(
            status_code=400,
            detail="You must have at least one address"
        )

    address = db.query(Address).filter(
        Address.id == address_id,
        Address.user_id == current_user.id
    ).first()

    if not address:
        raise HTTPException(status_code=404)
    
    if address.is_default:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete default address"
        )


    db.delete(address)
    db.commit()
