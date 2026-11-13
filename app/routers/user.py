
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth.security import hash_password
from app.models.model import User
from app.schemas.user import ResetPasswordRequest, ResetPasswordRequest, UserUpdate
from app.schemas.user import UserUpdate
from database import get_db

from app.auth.dependencies import get_current_user
from app.auth.permissions import require_permission

from app.auth.permissions import (
    get_user_role_names,
    get_user_permission_codes
)


router = APIRouter(
    prefix="/users",
    tags=["User Management"]
)


# CURRENT USER PROFILE

@router.get("/me")
def get_my_profile(

    current_user: User = Depends(get_current_user)

):

    return {

        "user_id": current_user.user_id,

        "employee_id": current_user.employee_id,

        "email": current_user.email,

        "is_active": current_user.is_active

    }


# CURRENT USER ROLES

@router.get("/my-roles")
def get_my_roles(

    current_user: User = Depends(get_current_user)

):

    return {

        "user_id": current_user.user_id,

        "email": current_user.email,

        "roles": sorted(
            get_user_role_names(current_user)
        )

    }


# CURRENT USER PERMISSIONS

@router.get("/my-permissions")
def get_my_permissions(

    current_user: User = Depends(get_current_user)

):

    return {

        "user_id": current_user.user_id,

        "email": current_user.email,

        "permissions": sorted(
            get_user_permission_codes(current_user)
        )

    }

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session



router = APIRouter(
    prefix="/users",
    tags=["User Management"]
)


# API 1: Get all users
@router.get("/")
def get_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission("user.read")
    )
):

    users = (
        db.query(User)
        .order_by(User.user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return {
        "message": "Users retrieved successfully",
        "total": len(users),
        "users": [
            {
                "user_id": user.user_id,
                "employee_id": user.employee_id,
                "email": user.email,
                "is_active": user.is_active
            }
            for user in users
        ]
    }


# API 2: Get user by ID
@router.get("/{user_id}")
def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission("user.read")
    )
):

    user = (
        db.query(User)
        .filter(User.user_id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return {
        "message": "User retrieved successfully",
        "user": {
            "user_id": user.user_id,
            "employee_id": user.employee_id,
            "email": user.email,
            "is_active": user.is_active
        }
    }
#patch user endpoint

@router.patch("/{user_id}")
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission("user.update")
    )
):

    user = db.query(User).filter(
        User.user_id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    update_data = user_data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No fields provided for update"
        )

    if "email" in update_data:
        if not update_data["email"].strip():
            raise HTTPException(
                status_code=400,
                detail="Email cannot be empty"
            )

        existing_user = db.query(User).filter(
            User.email == update_data["email"],
            User.user_id != user_id
        ).first()

        if existing_user:
            raise HTTPException(
                status_code=409,
                detail="Email already exists"
            )

    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    return {
        "message": "User updated successfully",
        "user": {
            "user_id": user.user_id,
            "employee_id": user.employee_id,
            "email": user.email,
            "is_active": user.is_active
        }
    }

#reset password endpoint

@router.post("/{user_id}/reset-password")
def reset_user_password(
    user_id: int,
    password_data: ResetPasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission("user.reset_password")
    )
):

    user = db.query(User).filter(
        User.user_id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # Hash the new password using Argon2
    user.password_hash = hash_password(
        password_data.new_password
    )

    db.commit()

    return {
        "message": "Password reset successfully",
        "user_id": user.user_id
    }