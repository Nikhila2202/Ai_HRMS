
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db

from app.models.model import LeaveBalance

from app.schemas.leave_balance import (
    LeaveBalanceUpdate,
    LeaveBalanceResponse
)

from app.auth.dependencies import get_current_user
from app.auth.permissions import require_permission


router = APIRouter(
    prefix="/leave/balances",
    tags=["Leave Balances"]
)


# 1. GET MY LEAVE BALANCES

@router.get("/me")
def get_my_leave_balances(
    db: Session = Depends(get_db),
    current_user=Depends(
        require_permission("leave_balance.read_own")
    )
):

    if not current_user.employee_id:
        raise HTTPException(
            status_code=400,
            detail="User is not linked to an employee"
        )

    balances = db.query(LeaveBalance).filter(
        LeaveBalance.employee_id == current_user.employee_id
    ).all()

    return balances


# 2. GET LEAVE BALANCES BY EMPLOYEE ID

@router.get("/employee/{employee_id}")
def get_employee_leave_balances(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_permission("leave_balance.read")
    )
):

    balances = db.query(LeaveBalance).filter(
        LeaveBalance.employee_id == employee_id
    ).all()

    if not balances:
        raise HTTPException(
            status_code=404,
            detail="Leave balances not found for this employee"
        )

    return balances


# 3. PATCH LEAVE BALANCE BY BALANCE ID

@router.patch("/{balance_id}", response_model=LeaveBalanceResponse)
def update_leave_balance(
    balance_id: int,
    data: LeaveBalanceUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_permission("leave_balance.update")
    )
):
    balance = db.query(LeaveBalance).filter(
        LeaveBalance.leave_balance_id == balance_id
    ).first()

    if not balance:
        raise HTTPException(
            status_code=404,
            detail="Leave balance not found"
        )

    update_data = data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No fields provided for update"
        )

    for key, value in update_data.items():
        setattr(balance, key, value)

    db.commit()
    db.refresh(balance)

    return balance