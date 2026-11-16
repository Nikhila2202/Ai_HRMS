
from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from typing import Optional


# RESPONSE SCHEMA

class LeaveBalanceResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    leave_balance_id: int
    employee_id: int
    leave_type: str
    entitlement_days: Decimal
    used_days: Decimal
    balance_year: int


# UPDATE SCHEMA

class LeaveBalanceUpdate(BaseModel):

    entitlement_days: Optional[Decimal] = None
    used_days: Optional[Decimal] = None
