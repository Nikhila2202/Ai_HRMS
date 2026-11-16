from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import date
from decimal import Decimal


# CREATE SCHEMA
class LeaveEntitlementCreate(BaseModel):

    leave_type_id: int

    employment_category: str = "all"

    entitlement_days: Decimal = Field(ge=0)

    effective_from: date

    effective_to: Optional[date] = None

    is_active: bool = True


# UPDATE SCHEMA
class LeaveEntitlementUpdate(BaseModel):

    leave_type_id: Optional[int] = None

    employment_category: Optional[str] = None

    entitlement_days: Optional[Decimal] = Field(
        default=None,
        ge=0
    )

    effective_from: Optional[date] = None

    effective_to: Optional[date] = None

    is_active: Optional[bool] = None


# RESPONSE SCHEMA
class LeaveEntitlementResponse(BaseModel):

    entitlement_rule_id: int

    leave_type_id: int

    employment_category: str

    entitlement_days: Decimal

    effective_from: date

    effective_to: Optional[date]

    is_active: bool

    model_config = ConfigDict(from_attributes=True)