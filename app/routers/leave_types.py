
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database import get_db

from app.auth.permissions import require_permission
from app.models.model import LeaveType

from app.schemas.leave import (
    LeaveTypeCreate,
    LeaveTypeUpdate,
    LeaveTypeResponse
)


router = APIRouter(
    prefix="/leave-types",
    tags=["Leave Types"]
)


# =====================================
# POST - CREATE LEAVE TYPE
# Admin and HR Manager
# =====================================

@router.post(
    "/",
    response_model=LeaveTypeResponse,
    status_code=status.HTTP_201_CREATED
)
def create_leave_type(

    leave_data: LeaveTypeCreate,

    db: Session = Depends(get_db),

    current_user=Depends(
        require_permission("leave_type.create")
    )
):

    # Check duplicate leave type code

    existing_leave = db.query(LeaveType).filter(
     LeaveType.leave_type_code == leave_data.leave_type_code
    ).first()

    if existing_leave:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Leave type code already exists"
        )

    # Create leave type

    new_leave_type = LeaveType(
        **leave_data.model_dump()
    )

    try:
        db.add(new_leave_type)
        db.commit()
        db.refresh(new_leave_type)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Leave type already exists"
        )

    return new_leave_type


# =====================================
# GET - ALL LEAVE TYPES
# Admin, HR Manager and Employee
# =====================================

@router.get(
    "/",
    response_model=list[LeaveTypeResponse],
    status_code=status.HTTP_200_OK
)
def get_all_leave_types(

    db: Session = Depends(get_db),

    current_user=Depends(
        require_permission("leave_type.read")
    )
):

    leave_types = db.query(LeaveType).order_by(
        LeaveType.leave_type_id
    ).all()

    return leave_types


# =====================================
# GET - LEAVE TYPE BY ID
# Admin, HR Manager and Employee
# =====================================

@router.get(
    "/{leave_type_id}",
    response_model=LeaveTypeResponse,
    status_code=status.HTTP_200_OK
)
def get_leave_type_by_id(

    leave_type_id: int,

    db: Session = Depends(get_db),

    current_user=Depends(
        require_permission("leave_type.read")
    )
):

    leave_type = db.get(
        LeaveType,
        leave_type_id
    )

    if not leave_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave type not found"
        )

    return leave_type


# =====================================
# PATCH - UPDATE LEAVE TYPE
# Admin and HR Manager
# =====================================

@router.patch(
    "/{leave_type_id}",
    response_model=LeaveTypeResponse,
    status_code=status.HTTP_200_OK
)
def update_leave_type(

    leave_type_id: int,

    leave_data: LeaveTypeUpdate,

    db: Session = Depends(get_db),

    current_user=Depends(
        require_permission("leave_type.update")
    )
):

    # Check leave type exists

    leave_type = db.get(
        LeaveType,
        leave_type_id
    )

    if not leave_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave type not found"
        )

    # Get only fields provided in request

    update_data = leave_data.model_dump(
        exclude_unset=True
    )

    # Check duplicate leave type code

    if "leave_type_code" in update_data:

        existing_leave = db.query(LeaveType).filter(
            LeaveType.leave_type_code == update_data["leave_type_code"],
            LeaveType.leave_type_id != leave_type_id
        ).first()

        if existing_leave:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Leave type code already exists"
            )

    # Update fields

    for field, value in update_data.items():
        setattr(leave_type, field, value)

    try:
        db.commit()
        db.refresh(leave_type)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Leave type update conflicts with existing data"
        )

    return leave_type
