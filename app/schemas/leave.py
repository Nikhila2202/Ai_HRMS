# app/schemas/leave_type.py

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


# POST REQUEST

# POST REQUEST
class LeaveTypeCreate(BaseModel):

    leave_type_name: str = Field(min_length=2, max_length=100)
    leave_type_code: str = Field(min_length=2, max_length=20)

    description: Optional[str] = None
    is_paid: bool = True
    requires_approval: bool = True
    min_notice_calendar_days: int = Field(default=0, ge=0)
    max_consecutive_days: Optional[int] = Field(default=None, gt=0)
    max_days_per_year: int = Field(gt=0)
    is_active: bool = True


# PATCH REQUEST
class LeaveTypeUpdate(BaseModel):

    leave_type_name: Optional[str] = Field(
        default=None, min_length=2, max_length=100
    )
    leave_type_code: Optional[str] = Field(
        default=None, min_length=2, max_length=20
    )
    description: Optional[str] = None
    is_paid: Optional[bool] = None
    requires_approval: Optional[bool] = None
    min_notice_calendar_days: Optional[int] = Field(
        default=None, ge=0
    )
    max_consecutive_days: Optional[int] = Field(
        default=None, gt=0
    )
    max_days_per_year: Optional[int] = Field(
        default=None, gt=0
    )
    is_active: Optional[bool] = None


# RESPONSE
class LeaveTypeResponse(BaseModel):

    leave_type_id: int
    leave_type_name: str
    leave_type_code: str
    description: Optional[str] = None
    is_paid: bool
    requires_approval: bool
    min_notice_calendar_days: int
    max_consecutive_days: Optional[float] = None
    max_days_per_year: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
