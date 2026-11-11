
from pydantic import BaseModel, Field


class EmployeeAccountCreate(BaseModel):

    employee_id: int = Field(gt=0)

    initial_password: str = Field(
        min_length=12,
        max_length=128
    )
