from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db

from app.models.model import (
    LeaveEntitlementRule,
    LeaveType
)

from app.schemas.leave_entitlement import (
    LeaveEntitlementCreate,
    LeaveEntitlementUpdate,
    LeaveEntitlementResponse
)


router = APIRouter(
    prefix="/leave-entitlements",
    tags=["Leave Entitlements"]
)


# =====================================
# POST - CREATE LEAVE ENTITLEMENT
# =====================================

@router.post(
    "/",
    response_model=LeaveEntitlementResponse,
    status_code=status.HTTP_201_CREATED
)
def create_leave_entitlement(
    entitlement_data: LeaveEntitlementCreate,
    db: Session = Depends(get_db)
):

    # Check whether leave type exists
    leave_type = db.query(LeaveType).filter(
        LeaveType.leave_type_id == entitlement_data.leave_type_id
    ).first()

    if not leave_type:
        raise HTTPException(
            status_code=404,
            detail="Leave type not found"
        )

    # Validate dates
    if (
        entitlement_data.effective_to is not None
        and entitlement_data.effective_to < entitlement_data.effective_from
    ):
        raise HTTPException(
            status_code=400,
            detail="Effective to date cannot be earlier than effective from date"
        )

    # Create entitlement
    new_entitlement = LeaveEntitlementRule(
        **entitlement_data.model_dump()
    )

    db.add(new_entitlement)
    db.commit()
    db.refresh(new_entitlement)

    return new_entitlement


# =====================================
# GET - ALL LEAVE ENTITLEMENTS
# =====================================

@router.get(
    "/",
    response_model=list[LeaveEntitlementResponse]
)
def get_leave_entitlements(
    db: Session = Depends(get_db)
):

    entitlements = db.query(
        LeaveEntitlementRule
    ).order_by(
        LeaveEntitlementRule.entitlement_rule_id
    ).all()

    return entitlements


# =====================================
# PATCH - UPDATE LEAVE ENTITLEMENT
# =====================================

@router.patch(
    "/{entitlement_rule_id}",
    response_model=LeaveEntitlementResponse
)
def update_leave_entitlement(
    entitlement_rule_id: int,
    entitlement_data: LeaveEntitlementUpdate,
    db: Session = Depends(get_db)
):

    # Find entitlement rule
    entitlement = db.query(
        LeaveEntitlementRule
    ).filter(
        LeaveEntitlementRule.entitlement_rule_id == entitlement_rule_id
    ).first()

    if not entitlement:
        raise HTTPException(
            status_code=404,
            detail="Leave entitlement rule not found"
        )

    # Get only fields supplied by the user
    update_data = entitlement_data.model_dump(
        exclude_unset=True
    )

    # Check leave type if it is being changed
    if "leave_type_id" in update_data:

        leave_type = db.query(LeaveType).filter(
            LeaveType.leave_type_id == update_data["leave_type_id"]
        ).first()

        if not leave_type:
            raise HTTPException(
                status_code=404,
                detail="Leave type not found"
            )

    # Validate final dates, including unchanged existing values
    effective_from = update_data.get(
        "effective_from",
        entitlement.effective_from
    )

    effective_to = update_data.get(
        "effective_to",
        entitlement.effective_to
    )

    if (
        effective_to is not None
        and effective_to < effective_from
    ):
        raise HTTPException(
            status_code=400,
            detail="Effective to date cannot be earlier than effective from date"
        )

    # Update fields
    for key, value in update_data.items():
        setattr(entitlement, key, value)

    db.commit()
    db.refresh(entitlement)

    return entitlement