from fastapi import FastAPI

from app.routers import (
    auth,
    employee_signup,
    user,
    protected
)

app = FastAPI(
    title="AI Powered HRMS",
    description="AI Powered Human Resource Management System",
    version="1.0.0"
)

app.include_router(auth.router)
app.include_router(employee_signup.router)
app.include_router(user.router)
app.include_router(protected.router)



