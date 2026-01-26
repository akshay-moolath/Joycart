from fastapi import APIRouter, Depends,Form,Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.db.db import get_db
from fastapi.templating import Jinja2Templates
from app.auth import get_current_user,create_access_token
from app.db.models import User
from app.user.services.user_services import create_user,authenticate_user,home,profile,update_profile,add_address,edit_address,delete_address


router = APIRouter()
pages_router = APIRouter()

templates = Jinja2Templates(directory="templates")

###############################REGISTER#########################################

@router.post("/register")
def create_user_endpoint(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    create_user(username,email,password,db)

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
def login_user_endpoint(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = authenticate_user(username, password, db)

    if not user:
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
        samesite="lax",
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
def home_endpoint(
    request: Request,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    products = home(current_user,db)

    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "products": products,
            "current_user": current_user
        }
    )



@pages_router.get("/profile")
def profile_endpoint(
    request: Request,
    section: str | None = None,
    add: bool = False,
    edit: int | None = None,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    (addresses,address_to_edit) = profile(section,edit,current_user,db)

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
def update_profile_endpoint(
    username: str = Form(None),
    email: str = Form(None),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    update_profile(username,email,current_user,db)

    return RedirectResponse(
        url="/profile",
        status_code=303
    )
    



################################ ADD,DELETE AND EDIT ADDRESS#############################

@router.post("/address/add")
def add_address_endpoint(
    current_user: User = Depends(get_current_user),
    name: str = Form(...),
    phone: str = Form(...),
    address_line1: str = Form(...),
    address_line2: str = Form(None),
    city: str = Form(...),
    state: str = Form(...),
    pincode: str = Form(...),
    is_default: bool = Form(False),
    redirect_to: str = Form(None),
    db: Session = Depends(get_db)
    
):
    add_address(current_user,name,phone,address_line1,address_line2,city,state,pincode,is_default,db)

    return RedirectResponse(redirect_to or
        "/profile?section=address",
        status_code=303
    )

@pages_router.get('/address/add')
def add_address(request: Request,
                checkout_id: str | None = None,
                current_user = Depends(get_current_user)):
    return templates.TemplateResponse(
        "checkout_address_add.html",
        {"request":request,
         "checkout_id": checkout_id,
         "current_user":current_user}
        )


@router.post("/address/edit/{address_id}")
def edit_address_endpoint(
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
    edit_address(address_id,name,phone,city,state,address_line1,address_line2,pincode,current_user,db)

    return RedirectResponse("/profile?section=address", status_code=302)


@router.post("/address/delete/{address_id}")
def delete_address_endpoint(
    address_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    delete_address(address_id,current_user,db)

    return RedirectResponse(
        "/profile?section=address",
        status_code=303
    )



