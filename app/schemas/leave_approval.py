
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class LeaveDecisionRequest(BaseModel):
    decision: str
    comments: Optional[str] = None


class LeaveApprovalResponse(BaseModel):
    leave_approval_id: int
    leave_request_id: int
    approver_employee_id: int
    decision: str
    comments: Optional[str] = None
    decided_at: Optional[datetime] = None

    class Config:
        from_attributes = True
