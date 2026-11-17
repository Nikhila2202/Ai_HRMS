from fastapi import FastAPI

from app.routers import (
    auth,
    employee,
    timesheet,
    user,
    protected,
    department,
    roles,
    role_permissions,leave_types, leave_entitlement, leave_balance, leave_request,leave_approval, holiday, hr_document
 ,timesheet, ai_assistant, audit_log
)


app = FastAPI(
    title="AI Powered HRMS",
    description="AI Powered Human Resource Management System",
    version="1.0.0"
)


# Register routers

app.include_router(auth.router)
app.include_router(employee.router)
app.include_router(user.router)
app.include_router(protected.router)
app.include_router(department.router)
app.include_router(roles.router)
app.include_router(role_permissions.router)
app.include_router(leave_types.router)
app.include_router(leave_entitlement.router)
app.include_router(leave_balance.router)
app.include_router(leave_request.router)
app.include_router(leave_approval.router)
app.include_router(holiday.router)
app.include_router(hr_document.router)
app.include_router(timesheet.router)
app.include_router(ai_assistant.router)
app.include_router(audit_log.router)












