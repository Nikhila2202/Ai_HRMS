
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Query
)

from sqlalchemy.orm import Session

from database import get_db

from app.models.model import (
    AuditLog,
    User
)

from app.auth.dependencies import get_current_user

from app.schemas.audit_log import AuditLogResponse


router = APIRouter(
    prefix="/audit-logs",
    tags=["Audit Logs"]
)


# =====================================
# HELPER: CHECK AUDIT LOG PERMISSION
# =====================================

def check_audit_permission(current_user: User):

    user_permissions = set()

    for user_role in current_user.roles:
        for role_permission in user_role.role.permissions:

            user_permissions.add(
                role_permission.permission.permission_code
            )

    if "audit_log.read" not in user_permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view audit logs"
        )


# =====================================
# 1. GET ALL AUDIT LOGS
# =====================================

@router.get(
    "",
    response_model=list[AuditLogResponse]
)
def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user)
):

    # CHECK PERMISSION

    check_audit_permission(current_user)

    # FETCH AUDIT LOGS

    audit_logs = db.query(AuditLog).order_by(
        AuditLog.created_at.desc()
    ).offset(
        skip
    ).limit(
        limit
    ).all()

    return audit_logs


# =====================================
# 2. GET AUDIT LOG BY ID
# =====================================

@router.get(
    "/{audit_log_id}",
    response_model=AuditLogResponse
)
def get_audit_log_by_id(
    audit_log_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user)
):

    # CHECK PERMISSION

    check_audit_permission(current_user)

    # FIND AUDIT LOG

    audit_log = db.query(AuditLog).filter(
        AuditLog.audit_log_id == audit_log_id
    ).first()

    if not audit_log:
        raise HTTPException(
            status_code=404,
            detail="Audit log not found"
        )

    return audit_log
