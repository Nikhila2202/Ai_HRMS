
from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user

from app.auth.permissions import (
    require_role,
    require_any_role,
    require_permission
)


router = APIRouter(
    prefix="/protected",
    tags=["Protected APIs"]
)


# API 1: Any authenticated user

@router.get("/dashboard")
def dashboard(

    current_user=Depends(get_current_user)

):

    return {

        "message": "Authenticated access granted",

        "user_id": current_user.user_id

    }


# API 2: Admin only

@router.get("/admin-dashboard")
def admin_dashboard(

    current_user=Depends(
        require_role("Admin")
    )

):

    return {

        "message": "Welcome Admin"

    }


# API 3: Admin or HR Manager

@router.get("/hr-dashboard")
def hr_dashboard(

    current_user=Depends(
        require_any_role(
            "Admin",
            "HR Manager"
        )
    )

):

    return {

        "message": "HR access granted"

    }


# API 4: Employee view permission

@router.get("/employees")
def view_employees(

    current_user=Depends(
        require_permission("employee.view")
    )

):

    return {

        "message": "Employee view permission granted"

    }


# API 5: Employee delete permission

@router.delete("/employees/{employee_id}")
def delete_employee(

    employee_id: int,

    current_user=Depends(
        require_permission("employee.delete")
    )

):

    return {

        "message": "Employee delete permission granted",

        "employee_id": employee_id

    }
