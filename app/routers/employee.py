

from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.auth.dependencies import get_current_user
from database import get_db

from app.models.model import (
    Employee,
    User,
    Role,
    UserRole
)

from app.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeUpdate

from app.auth.security import hash_password

from app.auth.permissions import require_permission


router = APIRouter(
    prefix="/employee",
    tags=["Employee Account Management"]
)


@router.post(
    "/create",
    status_code=status.HTTP_201_CREATED
)
def create_employee_account(

    data: EmployeeCreate,

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

#get employees

@router.get("/")
def get_all_employees(

    skip: int = 0,
    limit: int = 50,

    db: Session = Depends(get_db),

    current_user=Depends(
        require_permission("employee.read")
    )

):

    if skip < 0 or limit < 1 or limit > 100:
        raise HTTPException(
            status_code=400,
            detail="Invalid pagination values"
        )

    employees = (
        db.query(Employee)
        .order_by(Employee.employee_id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return {
        "message": "Employees retrieved successfully",
        "total": len(employees),

        "employees": [
            {
                "employee_id": emp.employee_id,
                "employee_code": emp.employee_code,
                "full_name": emp.full_name,
                "email": emp.email,
                "department": emp.department,
                "job_title": emp.job_title,
                "hire_date": emp.hire_date,
                "is_active": emp.is_active,
                "department_id": emp.department_id,
                "manager_employee_id": emp.manager_employee_id
            }
            for emp in employees
        ]
    }

#get employee by id

@router.get("/me")
def get_my_employee_profile(

    db: Session = Depends(get_db),

    current_user=Depends(get_current_user)

):

    if current_user.employee_id is None:
        raise HTTPException(
            status_code=404,
            detail="No employee profile linked to this account"
        )

    employee = db.query(Employee).filter(
        Employee.employee_id == current_user.employee_id
    ).first()

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee profile not found"
        )

    return {
        "message": "Your employee profile retrieved successfully",

        "employee": {
            "employee_id": employee.employee_id,
            "employee_code": employee.employee_code,
            "full_name": employee.full_name,
            "email": employee.email,
            "department": employee.department,
            "job_title": employee.job_title,
            "hire_date": employee.hire_date,
            "is_active": employee.is_active,
            "department_id": employee.department_id,
            "manager_employee_id": employee.manager_employee_id
        }
    }

#get employee by id

@router.get("/{employee_id}")
def get_employee_by_id(

    employee_id: int,

    db: Session = Depends(get_db),

    current_user=Depends(
        require_permission("employee.read")
    )

):

    employee = db.query(Employee).filter(
        Employee.employee_id == employee_id
    ).first()

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )

    return {
        "message": "Employee retrieved successfully",

        "employee": {
            "employee_id": employee.employee_id,
            "employee_code": employee.employee_code,
            "full_name": employee.full_name,
            "email": employee.email,
            "department": employee.department,
            "job_title": employee.job_title,
            "hire_date": employee.hire_date,
            "is_active": employee.is_active,
            "department_id": employee.department_id,
            "manager_employee_id": employee.manager_employee_id
        }
    }

#patch employee endpoint
from sqlalchemy.exc import IntegrityError


@router.patch("/{employee_id}")
def update_employee(

    employee_id: int,

    employee_data: EmployeeUpdate,

    db: Session = Depends(get_db),

    current_user=Depends(
        require_permission("employee.update")
    )

):

    employee = db.query(Employee).filter(
        Employee.employee_id == employee_id
    ).first()

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )

    update_data = employee_data.model_dump(
        exclude_unset=True
    )

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No fields provided for update"
        )

    # Validate required fields if supplied
    for field in ["employee_code", "full_name", "email", "is_active"]:
        if field in update_data and update_data[field] is None:
            raise HTTPException(
                status_code=400,
                detail=f"{field} cannot be null"
            )

    # Validate empty text fields
    for field in ["employee_code", "full_name", "email"]:
        if field in update_data:
            update_data[field] = update_data[field].strip()

            if not update_data[field]:
                raise HTTPException(
                    status_code=400,
                    detail=f"{field} cannot be empty"
                )

    # Check duplicate email
    if "email" in update_data:

        existing_email = db.query(Employee).filter(
            Employee.email == update_data["email"],
            Employee.employee_id != employee_id
        ).first()

        if existing_email:
            raise HTTPException(
                status_code=409,
                detail="Email already exists"
            )

    # Check duplicate employee code
    if "employee_code" in update_data:

        existing_code = db.query(Employee).filter(
            Employee.employee_code == update_data["employee_code"],
            Employee.employee_id != employee_id
        ).first()

        if existing_code:
            raise HTTPException(
                status_code=409,
                detail="Employee code already exists"
            )

    try:

        for field, value in update_data.items():
            setattr(employee, field, value)

        db.commit()
        db.refresh(employee)

        return {
            "message": "Employee updated successfully",

            "employee": {
                "employee_id": employee.employee_id,
                "employee_code": employee.employee_code,
                "full_name": employee.full_name,
                "email": employee.email,
                "department": employee.department,
                "job_title": employee.job_title,
                "hire_date": employee.hire_date,
                "is_active": employee.is_active,
                "department_id": employee.department_id,
                "manager_employee_id": employee.manager_employee_id
            }
        }

    except IntegrityError:

        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Database constraint violation"
        )