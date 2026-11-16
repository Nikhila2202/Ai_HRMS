
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db

from app.models.model import (
    LeaveApproval,
    LeaveRequest,
    User
)

from app.auth.dependencies import get_current_user

from app.schemas.leave_approval import (
    LeaveDecisionRequest,
    LeaveApprovalResponse
)


router = APIRouter(
    prefix="/leave",
    tags=["Leave Approvals"]
)


# CHECK PERMISSION

def has_leave_approval_permission(user: User):

    for user_role in user.roles:
        for role_permission in user_role.role.permissions:

            if (
                role_permission.permission.permission_code
                == "leave.approve"
            ):
                return True

    return False


# GET PENDING APPROVALS

@router.get("/approvals/pending")
def get_pending_approvals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if not current_user.employee_id:
        raise HTTPException(
            status_code=403,
            detail="User is not linked to an employee"
        )

    authorized = has_leave_approval_permission(current_user)

    query = db.query(LeaveApproval).filter(
        LeaveApproval.decision == "PENDING"
    )

    # Admin/HR with permission can see all pending approvals.
    # Other users see only approvals assigned to them.

    if not authorized:
        query = query.filter(
            LeaveApproval.approver_employee_id
            == current_user.employee_id
        )

    approvals = query.order_by(
        LeaveApproval.leave_approval_id.desc()
    ).all()

    return {
        "total": len(approvals),
        "pending_approvals": approvals
    }


# POST APPROVE / REJECT

@router.post(
    "/requests/{request_id}/decision",
    response_model=LeaveApprovalResponse
)
def decide_leave_request(
    request_id: int,
    decision_data: LeaveDecisionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    decision = decision_data.decision.upper()

    # Validate decision

    if decision not in ["APPROVED", "REJECTED"]:
        raise HTTPException(
            status_code=400,
            detail="Decision must be APPROVED or REJECTED"
        )

    if not current_user.employee_id:
        raise HTTPException(
            status_code=403,
            detail="User is not linked to an employee"
        )

    # Find leave request

    leave_request = db.query(LeaveRequest).filter(
        LeaveRequest.leave_request_id == request_id
    ).first()

    if not leave_request:
        raise HTTPException(
            status_code=404,
            detail="Leave request not found"
        )

    # Prevent self approval

    if leave_request.employee_id == current_user.employee_id:
        raise HTTPException(
            status_code=403,
            detail="You cannot approve your own leave request"
        )

    # Find pending approval

    approval = db.query(LeaveApproval).filter(
        LeaveApproval.leave_request_id == request_id,
        LeaveApproval.decision == "PENDING"
    ).with_for_update().first()

    if not approval:
        raise HTTPException(
            status_code=404,
            detail="No pending approval found"
        )

    # Check authorization

    authorized = has_leave_approval_permission(current_user)

    is_assigned_approver = (
        approval.approver_employee_id
        == current_user.employee_id
    )

    if not (authorized or is_assigned_approver):
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to approve this request"
        )

    try:

        # Update approval record

        approval.decision = decision
        approval.comments = decision_data.comments
        approval.decided_at = datetime.now(timezone.utc)

        # Update leave request status

        leave_request.status = decision

        db.commit()
        db.refresh(approval)

        return approval

    except Exception:
        db.rollback()
        raise
