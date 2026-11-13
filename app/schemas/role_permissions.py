from pydantic import BaseModel, Field


class AssignPermissionRequest(BaseModel):

    permission_id: int = Field(gt=0)