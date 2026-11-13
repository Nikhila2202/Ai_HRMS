# app/auth/permissions.py

from fastapi import APIRouter, Depends, HTTPException, status
from app.auth.dependencies import get_current_user
from sqlalchemy.orm import Session,selectinload

from app.auth.dependencies import get_current_user
from app.models.model import Permission, Role, RolePermission
from app.schemas.role_permissions import AssignPermissionRequest
from database import get_db


# GET USER ROLE NAMES
def get_user_role_names(current_user):

    role_names = set()

    for user_role in current_user.roles:

        if user_role.role:
            role_names.add(user_role.role.role_name)

    return role_names


# GET USER PERMISSION CODES
def get_user_permission_codes(current_user):

    permission_codes = set()

    for user_role in current_user.roles:

        role = user_role.role

        if role is None:
            continue

        for role_permission in role.permissions:

            permission = role_permission.permission

            if permission:
                permission_codes.add(permission.permission_code)

    return permission_codes


# SINGLE ROLE CHECKING
def require_role(required_role: str):

    def role_checker(
        current_user=Depends(get_current_user)
    ):

        user_roles = get_user_role_names(current_user)

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

        user_roles = get_user_role_names(current_user)

        if not user_roles.intersection(required_roles):

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role"
            )

        return current_user

    return role_checker


# PERMISSION CHECKING
def require_permission(permission_code: str):

    def permission_checker(
        current_user=Depends(get_current_user)
    ):

        user_permissions = get_user_permission_codes(current_user)

        if permission_code not in user_permissions:

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource"
            )

        return current_user

    return permission_checker


router = APIRouter(
    tags=["Role Permissions"]
)


# ==========================================
# GET PERMISSIONS BY ROLE ID
# ==========================================

@router.get(
    "/roles/{role_id}/permissions",
    status_code=status.HTTP_200_OK
)
def get_role_permissions(

    role_id: int,

    db: Session = Depends(get_db),

    current_user=Depends(
        require_permission("manage_users")
    )
):

    # Check whether role exists

    role = db.query(Role).filter(
        Role.role_id == role_id
    ).first()

    if not role:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )

    # Get permissions assigned to this role

    role_permissions = (
        db.query(RolePermission)
        .options(
            selectinload(RolePermission.permission)
        )
        .filter(
            RolePermission.role_id == role_id
        )
        .all()
    )

    permissions = []

    for role_permission in role_permissions:

        permission = role_permission.permission

        if permission:

            permissions.append({

                "permission_id": permission.permission_id,

                "permission_code": permission.permission_code,

                "description": permission.description

            })

    return {

        "role_id": role.role_id,

        "role_name": role.role_name,

        "total_permissions": len(permissions),

        "permissions": permissions

    }


# ==========================================
# ASSIGN PERMISSION TO ROLE
# ==========================================

@router.post(
    "/roles/{role_id}/permissions",
    status_code=status.HTTP_201_CREATED
)
def assign_permission_to_role(

    role_id: int,

    permission_data: AssignPermissionRequest,

    db: Session = Depends(get_db),

    current_user=Depends(
        require_permission("manage_users")
    )
):

    # Check whether role exists

    role = db.get(Role, role_id)

    if not role:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )

    # Check whether permission exists

    permission = db.get(
        Permission,
        permission_data.permission_id
    )

    if not permission:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )

    # Check duplicate assignment

    existing_assignment = db.get(
        RolePermission,
        (role_id, permission_data.permission_id)
    )

    if existing_assignment:

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Permission is already assigned to this role"
        )

    # Create role-permission assignment

    new_assignment = RolePermission(

        role_id=role_id,

        permission_id=permission_data.permission_id

    )

    try:

        db.add(new_assignment)

        db.commit()

    except Exception:

        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign permission"
        )

    return {

        "message": "Permission assigned successfully",

        "role_id": role.role_id,

        "role_name": role.role_name,

        "permission_id": permission.permission_id,

        "permission_code": permission.permission_code

    }