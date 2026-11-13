from fastapi import APIRouter, Depends, HTTPException, status
from opentelemetry.trace import Status
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, Field

from app.auth.permissions import require_permission
from app.schemas.roles import AssignRoleRequest, RoleCreate, RoleResponse, RoleUpdate, RoleUpdate
from database import get_db
from app.models.model  import Role, User, UserRole


router = APIRouter( 
    tags=["Roles Management"])


@router.post(
    "/roles",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED
)
def create_role(
    role_data: RoleCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("manage_roles"))
):

    existing_role = db.scalar(
        select(Role).where(
            Role.role_name == role_data.role_name
        )
    )

    if existing_role:
        raise HTTPException(
            status_code=400,
            detail="Role already exists"
        )

    new_role = Role(
        role_name=role_data.role_name,
        description=role_data.description
    )

    db.add(new_role)

    try:
        db.commit()
        db.refresh(new_role)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Role already exists"
        )

    return new_role


# --------------------------------
# 3. GET /roles
# Get all roles
# --------------------------------

@router.get("/roles", response_model=list[RoleResponse])
def get_all_roles(
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("manage_roles"))
):

    roles = db.scalars(
        select(Role).order_by(Role.role_id)
    ).all()

    return roles


# --------------------------------
# 4. GET /roles/{role_id}
# Get role by ID
# --------------------------------

@router.get("/roles/{role_id}", response_model=RoleResponse)
def get_role_by_id(
    role_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("manage_roles"))
):

    role = db.get(Role, role_id)

    if not role:
        raise HTTPException(
            status_code=404,
            detail="Role not found"
        )

    return role


# --------------------------------
# 5. PATCH /roles/{role_id}
# Update role by ID
# --------------------------------

@router.patch("/roles/{role_id}", response_model=RoleResponse)
def update_role(
    role_id: int,
    role_data: RoleUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("manage_roles"))
):

    role = db.get(Role, role_id)

    if not role:
        raise HTTPException(
            status_code=404,
            detail="Role not found"
        )

    update_data = role_data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No fields provided for update"
        )

    if "role_name" in update_data and update_data["role_name"] is None:
        raise HTTPException(
            status_code=400,
            detail="Role name cannot be null"
        )

    if "role_name" in update_data:
        existing_role = db.scalar(
            select(Role).where(
                Role.role_name == update_data["role_name"],
                Role.role_id != role_id
            )
        )

        if existing_role:
            raise HTTPException(
                status_code=409,
                detail="Role name already exists"
            )

    for field, value in update_data.items():
        setattr(role, field, value)

    try:
        db.commit()
        db.refresh(role)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Role name already exists"
        )

    return role


# --------------------------------
# 6. POST /users/{user_id}/roles
# Assign role to user
# --------------------------------

@router.post(
    "/users/{user_id}/roles",
    status_code=status.HTTP_201_CREATED
)
def assign_role_to_user(
    user_id: int,
    role_data: AssignRoleRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("manage_users"))
):

    # Check user exists

    user = db.get(User, user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=400,
            detail="Cannot assign a role to an inactive user"
        )

    # Check role exists

    role = db.get(Role, role_data.role_id)

    if not role:
        raise HTTPException(
            status_code=404,
            detail="Role not found"
        )

    # Check whether role is already assigned

    existing_assignment = db.get(
        UserRole,
        (user_id, role_data.role_id)
    )

    if existing_assignment:
        raise HTTPException(
            status_code=409,
            detail="User already has this role"
        )

    # Create user-role assignment

    new_assignment = UserRole(
        user_id=user_id,
        role_id=role_data.role_id
    )

    db.add(new_assignment)

    db.commit()

    return {
        "message": "Role assigned successfully",
        "user_id": user_id,
        "user_email": user.email,
        "role_id": role.role_id,
        "role_name": role.role_name
    }
