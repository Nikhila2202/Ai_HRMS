
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


# DOCUMENT TYPE RESPONSE

class HRDocumentTypeResponse(BaseModel):
    document_type_id: int
    document_type_code: str
    document_type_name: str
    description: Optional[str] = None
    requires_hr_approval: bool
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


# CREATE DOCUMENT REQUEST

class HRDocumentRequestCreate(BaseModel):
    document_type: str
    purpose: Optional[str] = None


# DOCUMENT REQUEST RESPONSE

class HRDocumentRequestResponse(BaseModel):
    document_request_id: int
    employee_id: int
    document_type: str
    purpose: Optional[str] = None
    status: str
    requested_at: datetime
    processed_by_employee_id: Optional[int] = None
    processed_at: Optional[datetime] = None
    remarks: Optional[str] = None
    document_reference: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class HRDocumentRequestUpdate(BaseModel):

    status: Optional[str] = None
    remarks: Optional[str] = None
    document_reference: Optional[str] = None