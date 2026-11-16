
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db

from app.models.model import (
    LeaveRequest,
    LeaveType
)

from app.schemas.leave_request import (
    LeaveRequestCreate,
    LeaveRequestResponse
)

from app.auth.dependencies import get_current_user
from app.auth.permissions import require_permission


router = APIRouter(
    prefix="/leave/requests",
    tags=["Leave Requests"]
)


# CHECK WHETHER USER HAS A PERMISSION

def user_has_permission(current_user, permission_code):

    for user_role in current_user.roles:
        for role_permission in user_role.role.permissions:

            if (
                role_permission.permission.permission_code
                == permission_code
            ):
                return True

    return False


# 1. POST - CREATE LEAVE REQUEST

@router.post(
    "",
    response_model=LeaveRequestResponse,
    status_code=status.HTTP_201_CREATED
)
def create_leave_request(
    data: LeaveRequestCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_permission("leave_request.create")
    )
):

    if not current_user.employee_id:
        raise HTTPException(
            status_code=400,
            detail="User is not linked to an employee"
        )

    # Check leave type exists

    leave_type = db.query(LeaveType).filter(
        LeaveType.leave_type_code == data.leave_type
    ).first()

    if not leave_type:
        raise HTTPException(
            status_code=404,
            detail="Leave type not found"
        )

    # Create leave request

    new_request = LeaveRequest(
        employee_id=current_user.employee_id,
        leave_type=data.leave_type,
        start_date=data.start_date,
        end_date=data.end_date,
        days_requested=data.days_requested,
        reason=data.reason
    )

    db.add(new_request)
    db.commit()
    db.refresh(new_request)

    return new_request


# 2. GET - MY LEAVE REQUESTS

@router.get(
    "/me",
    response_model=list[LeaveRequestResponse]
)
def get_my_leave_requests(
    db: Session = Depends(get_db),
    current_user=Depends(
        require_permission("leave_request.read_own")
    )
):

    if not current_user.employee_id:
        raise HTTPException(
            status_code=400,
            detail="User is not linked to an employee"
        )

    requests = db.query(LeaveRequest).filter(
        LeaveRequest.employee_id == current_user.employee_id
    ).order_by(
        LeaveRequest.submitted_at.desc()
    ).all()

    return requests


# 3. GET - LEAVE REQUEST BY REQUEST ID

@router.get(
    "/{request_id}",
    response_model=LeaveRequestResponse
)
def get_leave_request_by_id(
    request_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    leave_request = db.query(LeaveRequest).filter(
        LeaveRequest.leave_request_id == request_id
    ).first()

    if not leave_request:
        raise HTTPException(
            status_code=404,
            detail="Leave request not found"
        )

    # Employee can view only their own request.
    # Admin and HR Manager can view all requests.

    is_owner = (
        current_user.employee_id is not None
        and leave_request.employee_id == current_user.employee_id
    )

    has_hr_permission = (
        user_has_permission(current_user, "leave_request.read")
    )

    if not is_owner and not has_hr_permission:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to view this leave request"
        )

    return leave_request
