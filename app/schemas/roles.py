
from pydantic import BaseModel, Field


class RoleCreate(BaseModel):
    role_name: str = Field(..., min_length=2, max_length=100)
    description: str | None = None


class RoleUpdate(BaseModel):
    role_name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = None


class RoleResponse(BaseModel):
    role_id: int
    role_name: str
    description: str | None

    class Config:
        from_attributes = True


class AssignRoleRequest(BaseModel):
    role_id: int