from app.db.models import User
from fastapi import HTTPException

def get_users(db):

    users = db.query(User).all()

    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role,
            "is_blocked": u.is_blocked
        }
        for u in users
    ]

def block_users(user_id,db,admin):

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role == "admin":
        raise HTTPException(status_code=400, detail="Cannot block admin")

    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot block yourself")

    if user.is_blocked:
        return {"message": "User already blocked"}

    user.is_blocked = True
    db.commit()

    return {"message": f"User {user_id} blocked"}


def unblock_users(user_id,db,admin):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role == "admin":
        raise HTTPException(status_code=400, detail="Cannot unblock admin")

    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot unblock yourself")

    if not user.is_blocked:
        return {"message": "User already active"}

    user.is_blocked = False
    db.commit()

    return {"message": f"User {user_id} unblocked"}


def make_admin(user_id,db,admin):

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if user.role == "admin":
        return {
            "message": "User is already an admin"
        }

    if user.is_blocked:
        raise HTTPException(
            status_code=400,
            detail="Blocked user cannot be promoted to admin"
        )

    user.role = "admin"
    db.commit()

    return {
        "message": f"User {user_id} promoted to admin"
    }
