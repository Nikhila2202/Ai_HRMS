
from pydantic import BaseModel, Field, ConfigDict
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Literal


# CREATE TIMESHEET
class TimesheetCreate(BaseModel):
    period_start: date
    employee_comments: Optional[str] = None


# CREATE ENTRY
class TimesheetEntryCreate(BaseModel):
    work_date: date
    hours_worked: Decimal = Field(ge=0, le=24)
    task_description: str
    project_code: Optional[str] = None


# ENTRY RESPONSE
class TimesheetEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    timesheet_entry_id: int
    timesheet_id: int
    work_date: date
    hours_worked: Decimal
    task_description: str
    project_code: Optional[str]


# TIMESHEET RESPONSE
class TimesheetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    timesheet_id: int
    employee_id: int
    period_start: date
    period_end: date
    status: str
    total_hours: Decimal
    employee_comments: Optional[str] = None
    reviewer_comments: Optional[str] = None
    submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None


# APPROVE / REJECT
class TimesheetDecisionCreate(BaseModel):
    decision: Literal["approved", "rejected"]
    comments: Optional[str] = None
