from fastapi import FastAPI

from app.routers import (
    auth,
    employee,
    user,
    protected,
    department,
    roles,
    role_permissions,leave_types, leave_entitlement, leave_balance, leave_request,leave_approval, holiday
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











