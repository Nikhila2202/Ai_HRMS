
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class DepartmentCreate(BaseModel):
    department_name: str = Field(..., min_length=2, max_length=100)
    department_code: str = Field(..., min_length=2, max_length=20)
    parent_department_id: Optional[int] = None
    is_active: bool = True

    model_config = ConfigDict(extra="forbid")


class DepartmentUpdate(BaseModel):
    department_name: Optional[str] = Field(None, min_length=2, max_length=100)
    department_code: Optional[str] = Field(None, min_length=2, max_length=20)
    parent_department_id: Optional[int] = None
    is_active: Optional[bool] = None

    model_config = ConfigDict(extra="forbid")
