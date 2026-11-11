
from fastapi import Depends, HTTPException, status

from app.auth.dependencies import get_current_user


# GET USER ROLES

def get_user_role_names(current_user):

    role_names = set()

    for user_role in current_user.roles:

        if user_role.role:

            role_names.add(
                user_role.role.role_name
            )

    return role_names


# GET USER PERMISSIONS

def get_user_permission_codes(current_user):

    permission_codes = set()

    for user_role in current_user.roles:

        role = user_role.role

        if role is None:
            continue

        for role_permission in role.permissions:

            permission = role_permission.permission

            if permission:

                permission_codes.add(
                    permission.permission_code
                )

    return permission_codes


# SINGLE ROLE CHECKING

def require_role(required_role: str):

    def role_checker(

        current_user=Depends(get_current_user)

    ):

        user_roles = get_user_role_names(
            current_user
        )

        if required_role not in user_roles:

            raise HTTPException(

                status_code=status.HTTP_403_FORBIDDEN,

                detail="Insufficient role permission"

            )

        return current_user

    return role_checker


# MULTIPLE ROLE CHECKING

def require_any_role(*required_roles: str):

    def role_checker(

        current_user=Depends(get_current_user)

    ):

        user_roles = get_user_role_names(
            current_user
        )

        if not user_roles.intersection(required_roles):

            raise HTTPException(

                status_code=403,

                detail="Insufficient role"

            )

        return current_user

    return role_checker


# PERMISSION CHECKING

def require_permission(permission_code: str):

    def permission_checker(

        current_user=Depends(get_current_user)

    ):

        user_permissions = get_user_permission_codes(
            current_user
        )

        if permission_code not in user_permissions:

            raise HTTPException(

                status_code=403,

                detail="Permission denied"

            )

        return current_user

    return permission_checker
