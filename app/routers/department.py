
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database import get_db
from app.models.model import Department
from app.schemas.department import DepartmentCreate, DepartmentUpdate
from app.auth.permissions import require_permission


router = APIRouter(
    prefix="/departments",
    tags=["Department Management"]
)


# -----------------------------------
# POST: Create a department
# -----------------------------------

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_department(
    data: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("department.create"))
):

    existing_department = db.query(Department).filter(
        (Department.department_name == data.department_name) |
        (Department.department_code == data.department_code)
    ).first()

    if existing_department:
        raise HTTPException(
            status_code=409,
            detail="Department name or code already exists"
        )

    if data.parent_department_id is not None:
        parent = db.query(Department).filter(
            Department.department_id == data.parent_department_id
        ).first()

        if not parent:
            raise HTTPException(
                status_code=404,
                detail="Parent department not found"
            )

    new_department = Department(
        department_name=data.department_name,
        department_code=data.department_code,
        parent_department_id=data.parent_department_id,
        is_active=data.is_active
    )

    try:
        db.add(new_department)
        db.commit()
        db.refresh(new_department)

        return {
            "message": "Department created successfully",
            "department_id": new_department.department_id,
            "department_name": new_department.department_name,
            "department_code": new_department.department_code,
            "parent_department_id": new_department.parent_department_id,
            "is_active": new_department.is_active
        }

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Department code or name already exists, or a database constraint was violated"
        )


# -----------------------------------
# GET: Retrieve all departments
# -----------------------------------

@router.get("/")
def get_departments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("department.read"))
):

    departments = (
        db.query(Department)
        .order_by(Department.department_id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [
        {
            "department_id": dept.department_id,
            "department_name": dept.department_name,
            "department_code": dept.department_code,
            "parent_department_id": dept.parent_department_id,
            "is_active": dept.is_active
        }
        for dept in departments
    ]


# -----------------------------------
# GET: Retrieve department by ID
# -----------------------------------

@router.get("/{department_id}")
def get_department_by_id(
    department_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("department.read"))
):

    department = db.query(Department).filter(
        Department.department_id == department_id
    ).first()

    if not department:
        raise HTTPException(
            status_code=404,
            detail="Department not found"
        )

    return {
        "department_id": department.department_id,
        "department_name": department.department_name,
        "department_code": department.department_code,
        "parent_department_id": department.parent_department_id,
        "is_active": department.is_active
    }


# -----------------------------------
# PATCH: Update department by ID
# -----------------------------------

@router.patch("/{department_id}")
def update_department(
    department_id: int,
    data: DepartmentUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("department.update"))
):

    department = db.query(Department).filter(
        Department.department_id == department_id
    ).first()

    if not department:
        raise HTTPException(
            status_code=404,
            detail="Department not found"
        )

    update_data = data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No update data provided"
        )

    if "department_name" in update_data:
        duplicate = db.query(Department).filter(
            Department.department_name == update_data["department_name"],
            Department.department_id != department_id
        ).first()

        if duplicate:
            raise HTTPException(
                status_code=409,
                detail="Department name already exists"
            )

    if "department_code" in update_data:
        duplicate = db.query(Department).filter(
            Department.department_code == update_data["department_code"],
            Department.department_id != department_id
        ).first()

        if duplicate:
            raise HTTPException(
                status_code=409,
                detail="Department code already exists"
            )

    if "parent_department_id" in update_data:
        parent_id = update_data["parent_department_id"]

        if parent_id == department_id:
            raise HTTPException(
                status_code=400,
                detail="A department cannot be its own parent"
            )

        if parent_id is not None:
            parent = db.query(Department).filter(
                Department.department_id == parent_id
            ).first()

            if not parent:
                raise HTTPException(
                    status_code=404,
                    detail="Parent department not found"
                )

    try:
        for field, value in update_data.items():
            setattr(department, field, value)

        db.commit()
        db.refresh(department)

        return {
            "message": "Department updated successfully",
            "department_id": department.department_id,
            "department_name": department.department_name,
            "department_code": department.department_code,
            "parent_department_id": department.parent_department_id,
            "is_active": department.is_active
        }

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Department update violates a database constraint"
        )
