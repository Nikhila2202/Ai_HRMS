
from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class EmployeeCreate(BaseModel):

    employee_id: int = Field(gt=0)

    initial_password: str = Field(
        min_length=12,
        max_length=128
    )

class EmployeeUpdate(BaseModel):

    employee_code: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None
    department: Optional[str] = None
    job_title: Optional[str] = None
    hire_date: Optional[date] = None
    is_active: Optional[bool] = None
    department_id: Optional[int] = None
    manager_employee_id: Optional[int] = None

    model_config = ConfigDict(extra="forbid")
