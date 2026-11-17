
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    audit_log_id: int
    user_id: Optional[int] = None
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    description: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime
