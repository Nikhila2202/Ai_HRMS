

from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database import get_db

from app.models.model import (
    Employee,
    User,
    Role,
    UserRole
)

from app.schemas.employee_signup import EmployeeAccountCreate

from app.auth.security import hash_password

from app.auth.permissions import require_permission


router = APIRouter(
    prefix="/employee-accounts",
    tags=["Employee Account Management"]
)


@router.post(
    "/create",
    status_code=status.HTTP_201_CREATED
)
def create_employee_account(

    data: EmployeeAccountCreate,

    db: Session = Depends(get_db),

    current_user=Depends(
        require_permission("employee_account.create")
    )

):

    # 1. Find employee

    employee = db.query(Employee).filter(
        Employee.employee_id == data.employee_id
    ).first()

    if not employee:

        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )


    # 2. Check active employee

    if not employee.is_active:

        raise HTTPException(
            status_code=400,
            detail="Employee is inactive"
        )


    # 3. Check employee email

    if not employee.email:

        raise HTTPException(
            status_code=400,
            detail="Employee email is missing"
        )


    email = employee.email.strip().lower()


    # 4. Check existing account by employee ID

    existing_user = db.query(User).filter(
        User.employee_id == employee.employee_id
    ).first()

    if existing_user:

        raise HTTPException(
            status_code=409,
            detail="Employee account already exists"
        )


    # 5. Check duplicate email

    existing_email = db.query(User).filter(
        User.email == email
    ).first()

    if existing_email:

        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )


    # 6. Get default Employee role

    employee_role = db.query(Role).filter(
        Role.role_name == "Employee"
    ).first()

    if not employee_role:

        raise HTTPException(
            status_code=500,
            detail="Employee role not configured"
        )


    try:

        # 7. Hash password

        hashed_password = hash_password(
            data.initial_password
        )


        # 8. Create user

        new_user = User(

            employee_id=employee.employee_id,

            email=email,

            password_hash=hashed_password,

            is_active=True

        )

        db.add(new_user)

        # Generate user_id before creating user_role

        db.flush()


        # 9. Assign Employee role

        new_user_role = UserRole(

            user_id=new_user.user_id,

            role_id=employee_role.role_id

        )

        db.add(new_user_role)


        # 10. Commit both records together

        db.commit()

        db.refresh(new_user)


        return {

            "message": "Employee account created successfully",

            "user_id": new_user.user_id,

            "employee_id": new_user.employee_id,

            "email": new_user.email,

            "role": employee_role.role_name

        }


    except IntegrityError:

        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Duplicate account or database constraint violation"
        )

    except Exception:

        db.rollback()

        raise
