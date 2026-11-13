
from typing import Optional

from pydantic import BaseModel, ConfigDict


class UserUpdate(BaseModel):
    email: Optional[str] = None
    is_active: Optional[bool] = None

    model_config = ConfigDict(extra="forbid")

from pydantic import BaseModel, Field


class ResetPasswordRequest(BaseModel):
    new_password: str = Field(min_length=12, max_length=128)