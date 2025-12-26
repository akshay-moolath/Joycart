# app/crud/user.py
from fastapi import APIRouter, Depends, HTTPException,Form,Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.db import get_db
from fastapi.templating import Jinja2Templates
from app.auth import hash_password, verify_password, create_access_token,get_current_user
from app.models import User, Address,Order
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
        {"request": request}
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

    token = create_access_token({"sub": user.username})

    response = RedirectResponse(
        "/home",
        status_code=302
    )

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=60 * 60 * 24,
        samesite="lax",
        secure=False,
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
        {"request": request}
    )

@router.post("/logout")
def logout():
    response = RedirectResponse("/", status_code=302)
    response.delete_cookie("access_token")
    return response

##########################DASHBOARD AND PROFILE###############################

@pages_router.get("/home", dependencies=[Depends(get_current_user)])
def dashboard(
    request: Request,
    db: Session = Depends(get_db)
):
    products = list_products(db)

    return templates.TemplateResponse(
        "home.html",
        {"request": request, "products": products}
    )


@pages_router.get("/profile")
def profile(
    request: Request,
    current_user = Depends(get_current_user)
):
    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "username": current_user.username,
            "email": current_user.email
        }
    )

################################ ADD,DELETE AND EDIT ADDRESS#############################

@router.post("/address/add")
def add_address(current_user: User = Depends(get_current_user),
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

    return RedirectResponse("/address", status_code=302)

@pages_router.get('/address/add', dependencies=[Depends(get_current_user)])
def add_address(request: Request):
    return templates.TemplateResponse(
        "address_add.html",
        {"request":request}
        )

@pages_router.get("/address")
def get_address(request:Request,current_user: User = Depends(get_current_user),db:Session=Depends(get_db)):

    addresses = db.query(Address).filter(Address.user_id ==current_user.id).all()

    return templates.TemplateResponse(
        "address.html",{
            'request':request,
            'addresses':addresses
        }
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

    return RedirectResponse("/address", status_code=302)

@pages_router.get("/address/edit/{address_id}")
def edit_address_page(
    address_id: int,
    request: Request,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    address = db.query(Address).filter(
        Address.id == address_id,
        Address.user_id == current_user.id
    ).first()

    if not address:
        raise HTTPException(status_code=404)

    return templates.TemplateResponse(
        "address_edit.html",
        {
            "request": request,
            "address": address
        }
    )

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

    return RedirectResponse("/address", status_code=302)


from fastapi import Form, HTTPException

@router.post("/address/select")
def delivery_address(
    selected_address_id: int = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    address = db.query(Address).filter(
        Address.id == selected_address_id,
        Address.user_id == current_user.id
    ).first()

    if not address:
        raise HTTPException(status_code=404, detail="Address not found")

    
    shipping_address = {
        "name": address.name,
        "phone": address.phone,
        "address_line1": address.address_line1,
        "address_line2": address.address_line2,
        "city": address.city,
        "state": address.state,
        "pincode": address.pincode
    }

    
    order = db.query(Order).filter(
        Order.user_id == current_user.id,
        Order.status == "PENDING"
    ).first()

    if not order:
        raise HTTPException(status_code=400, detail="No active order")

    
    order.shipping_address = shipping_address
    db.commit()

    return RedirectResponse("/orders/summary", status_code=302)

@pages_router.get("/address/select")
def select_delivery_address(request:Request,current_user: User = Depends(get_current_user),db:Session=Depends(get_db)):

    addresses = db.query(Address).filter(Address.user_id ==current_user.id).all()

    return templates.TemplateResponse(
        "address_delivery.html",{
            'request':request,
            'addresses':addresses
        }
    )