
from fastapi import APIRouter, Depends

from app.models.model import User

from app.auth.dependencies import get_current_user

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
