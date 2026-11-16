
from pydantic import BaseModel, ConfigDict, Field, model_validator
from decimal import Decimal
from datetime import date, datetime
from typing import Optional


# POST REQUEST SCHEMA

class LeaveRequestCreate(BaseModel):

    leave_type: str
    start_date: date
    end_date: date
    days_requested: Decimal = Field(gt=0)
    reason: Optional[str] = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("End date cannot be before start date")
        return self


# RESPONSE SCHEMA

class LeaveRequestResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    leave_request_id: int
    employee_id: int
    leave_type: str
    start_date: date
    end_date: date
    days_requested: Decimal
    reason: Optional[str]
    status: str
    submitted_at: datetime
    updated_at: datetime
