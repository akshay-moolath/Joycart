# app/crud/user.py
from fastapi import APIRouter, Depends, HTTPException,Form,Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.db.db import get_db
from fastapi.templating import Jinja2Templates
from app.auth import hash_password, verify_password, create_access_token,get_current_user
from app.db.models import User, Address,Seller
from app.product import list_products


router = APIRouter()
pages_router = APIRouter()

templates = Jinja2Templates(directory="templates")

###############################REGISTER#########################################

@router.post("/register")
def create_user(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
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

    return RedirectResponse("/login", status_code=302)

@pages_router.get("/register")
def register(request: Request):
     
    token = request.cookies.get("access_token")

    if token:
        return RedirectResponse("/home", status_code=302)

    return templates.TemplateResponse(
        "register.html",
        {"request": request,
         "current_user": None}
    )

############################LOGIN AND LOGOUT#################################

@router.post("/login")
def login_user( username: str = Form(...),
    password: str = Form(...), 
    db: Session = Depends(get_db)):

    user = db.query(User).filter(
        User.username == username
    ).first()

    if not user or not verify_password(password, user.password):
        return RedirectResponse(
            "/login?error=1",
            status_code=302
        )

    token = create_access_token({"sub": str(user.id)})

    response = RedirectResponse(
        "/home",
        status_code=302
    )

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=60 * 60 * 24,
        samesite="none",
        secure=True,
        path="/"  
    )

    return response

@pages_router.get('/login')
def login(request: Request):
    token = request.cookies.get("access_token")

    if token:
        return RedirectResponse("/home", status_code=302)

    return templates.TemplateResponse(
        "login.html",
        {"request": request,
         "current_user": None}
    )

@router.post("/logout")
def logout():
    response = RedirectResponse("/", status_code=302)
    response.delete_cookie("access_token")
    return response

##########################DASHBOARD AND PROFILE###############################


@pages_router.get("/home", dependencies=[Depends(get_current_user)])
def home(
    request: Request,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    products = list_products(db)

    user = db.query(User).filter(User.id == current_user.id).first()

    if current_user.is_seller:
        seller = (
            db.query(Seller)
            .filter(Seller.user_id == current_user.id)
            .first()
        )

        if seller:
            products = [
                p for p in products
                if p.seller_id != seller.id
            ]

    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "products": products,
            "current_user": current_user
        }
    )



@pages_router.get("/profile")
def profile(
    request: Request,
    section: str | None = None,
    add: bool = False,
    edit: int | None = None,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
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

    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "username": current_user.username,
            "email": current_user.email,
            "section": section,
            "add": add,
            "edit": edit,
            "addresses": addresses,
            "address_to_edit": address_to_edit,
            "current_user":current_user
        }
    )
@router.post("/profile/update")
def update_profile(
    username: str = Form(None),
    email: str = Form(None),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
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

    return RedirectResponse(
        url="/profile",
        status_code=303
    )
    



################################ ADD,DELETE AND EDIT ADDRESS#############################

@router.post("/address/add")
def add_address(
    current_user: User = Depends(get_current_user),
    name: str = Form(...),
    phone: str = Form(...),
    address_line1: str = Form(...),
    address_line2: str = Form(None),
    city: str = Form(...),
    state: str = Form(...),
    pincode: str = Form(...),
    is_default: bool = Form(False),
    db: Session = Depends(get_db)
):
    
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

    return RedirectResponse(
        "/profile?section=address",
        status_code=303
    )

@router.post("/address/edit/{address_id}")
def edit_address(
    address_id: int,
    name: str = Form(...),
    phone: str = Form(...),
    address_line1: str = Form(...),
    address_line2: str = Form(None),
    city: str = Form(...),
    state: str = Form(...),
    pincode: str = Form(...),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    address = db.query(Address).filter(
        Address.id == address_id,
        Address.user_id == current_user.id
    ).first()

    address.name = name
    address.city = city
    address.phone = phone
    address.address_line1 = address_line1
    address.address_line2 = address_line2
    address.city = city
    address.state = state
    address.pincode = pincode
    
    db.commit()

    return RedirectResponse("/profile?section=address", status_code=302)


@router.post("/address/delete/{address_id}")
def delete_address(
    address_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
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

    db.delete(address)
    db.commit()

    return RedirectResponse(
        "/profile?section=address",
        status_code=303
    )



