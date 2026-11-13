from fastapi import APIRouter, HTTPException,status
from fastapi.params import Depends
from sqlalchemy.orm import Session, selectinload
from app.auth.permissions import require_permission
from app.models.model import Permission, Role, RolePermission
from app.schemas.role_permissions import AssignPermissionRequest
from database import get_db


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