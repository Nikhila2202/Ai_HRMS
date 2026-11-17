
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import timedelta, datetime, timezone

from database import get_db

from app.models.model import (
    Timesheet,
    TimesheetEntry,
    TimesheetApproval,
    User
)

from app.auth.dependencies import get_current_user

from app.schemas.timesheet import (
    TimesheetCreate,
    TimesheetEntryCreate,
    TimesheetEntryResponse,
    TimesheetResponse,
    TimesheetDecisionCreate
)


router = APIRouter(
    prefix="/timesheets",
    tags=["Timesheets"]
)


# =====================================
# HELPER: CHECK EMPLOYEE TIMESHEET
# =====================================

def get_employee_timesheet(
    db: Session,
    timesheet_id: int,
    current_user: User
):

    if not current_user.employee_id:
        raise HTTPException(
            status_code=403,
            detail="User is not linked to an employee"
        )

    timesheet = db.query(Timesheet).filter(
        Timesheet.timesheet_id == timesheet_id,
        Timesheet.employee_id == current_user.employee_id
    ).first()

    if not timesheet:
        raise HTTPException(
            status_code=404,
            detail="Timesheet not found"
        )

    return timesheet


# =====================================
# HELPER: CALCULATE TOTAL HOURS
# =====================================

def calculate_total_hours(
    db: Session,
    timesheet_id: int
):

    total = db.query(
        func.coalesce(
            func.sum(TimesheetEntry.hours_worked), 0
        )
    ).filter(
        TimesheetEntry.timesheet_id == timesheet_id
    ).scalar()

    timesheet = db.query(Timesheet).filter(
        Timesheet.timesheet_id == timesheet_id
    ).first()

    timesheet.total_hours = total

    return timesheet


# =====================================
# 1. POST - CREATE TIMESHEET
# =====================================

@router.post(
    "",
    response_model=TimesheetResponse,
    status_code=status.HTTP_201_CREATED
)
def create_timesheet(
    request_data: TimesheetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if not current_user.employee_id:
        raise HTTPException(
            status_code=403,
            detail="User is not linked to an employee"
        )

    period_end = request_data.period_start + timedelta(days=6)

    existing = db.query(Timesheet).filter(
        Timesheet.employee_id == current_user.employee_id,
        Timesheet.period_start == request_data.period_start
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Timesheet already exists for this week"
        )

    new_timesheet = Timesheet(
        employee_id=current_user.employee_id,
        period_start=request_data.period_start,
        period_end=period_end,
        status="draft",
        total_hours=0,
        employee_comments=request_data.employee_comments
    )

    db.add(new_timesheet)
    db.commit()
    db.refresh(new_timesheet)

    return new_timesheet


# =====================================
# 2. POST - ADD TIMESHEET ENTRY
# =====================================

@router.post(
    "/{timesheet_id}/entries",
    response_model=TimesheetEntryResponse,
    status_code=status.HTTP_201_CREATED
)
def create_timesheet_entry(
    timesheet_id: int,
    request_data: TimesheetEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    timesheet = get_employee_timesheet(
        db, timesheet_id, current_user
    )

    if timesheet.status != "draft":
        raise HTTPException(
            status_code=400,
            detail="Only draft timesheets accept entries"
        )

    if not (
        timesheet.period_start
        <= request_data.work_date
        <= timesheet.period_end
    ):
        raise HTTPException(
            status_code=400,
            detail="Work date must be within the timesheet period"
        )

    existing = db.query(TimesheetEntry).filter(
        TimesheetEntry.timesheet_id == timesheet_id,
        TimesheetEntry.work_date == request_data.work_date
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Entry already exists for this date"
        )

    new_entry = TimesheetEntry(
        timesheet_id=timesheet_id,
        work_date=request_data.work_date,
        hours_worked=request_data.hours_worked,
        task_description=request_data.task_description,
        project_code=request_data.project_code
    )

    db.add(new_entry)

    calculate_total_hours(db, timesheet_id)

    db.commit()
    db.refresh(new_entry)

    return new_entry


# =====================================
# 3. POST - SUBMIT TIMESHEET
# =====================================

@router.post(
    "/{timesheet_id}/submit",
    response_model=TimesheetResponse
)
def submit_timesheet(
    timesheet_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    timesheet = get_employee_timesheet(
        db, timesheet_id, current_user
    )

    if timesheet.status != "draft":
        raise HTTPException(
            status_code=400,
            detail="Only draft timesheets can be submitted"
        )

    total_entries = db.query(TimesheetEntry).filter(
        TimesheetEntry.timesheet_id == timesheet_id
    ).count()

    if total_entries == 0:
        raise HTTPException(
            status_code=400,
            detail="Add at least one entry before submitting"
        )

    calculate_total_hours(db, timesheet_id)

    timesheet.status = "submitted"
    timesheet.submitted_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(timesheet)

    return timesheet


# =====================================
# 4. POST - APPROVE / REJECT TIMESHEET
# =====================================

@router.post(
    "/{timesheet_id}/decision",
    response_model=TimesheetResponse
)
def timesheet_decision(
    timesheet_id: int,
    request_data: TimesheetDecisionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if not current_user.employee_id:
        raise HTTPException(
            status_code=403,
            detail="User is not linked to an employee"
        )

    # CHECK RBAC PERMISSION

    user_permissions = set()

    for user_role in current_user.roles:
        for role_permission in user_role.role.permissions:
            user_permissions.add(
                role_permission.permission.permission_code
            )

    if "timesheet.approve" not in user_permissions:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to decide timesheets"
        )

    # FIND TIMESHEET

    timesheet = db.query(Timesheet).filter(
        Timesheet.timesheet_id == timesheet_id
    ).first()

    if not timesheet:
        raise HTTPException(
            status_code=404,
            detail="Timesheet not found"
        )

    if timesheet.status != "submitted":
        raise HTTPException(
            status_code=400,
            detail="Only submitted timesheets can receive a decision"
        )

    if timesheet.employee_id == current_user.employee_id:
        raise HTTPException(
            status_code=403,
            detail="You cannot approve your own timesheet"
        )

    # UPDATE STATUS

    timesheet.status = request_data.decision
    timesheet.reviewer_comments = request_data.comments

    if request_data.decision == "approved":
        timesheet.approved_at = datetime.now(timezone.utc)

    # CREATE APPROVAL RECORD

    approval = TimesheetApproval(
        timesheet_id=timesheet_id,
        approver_employee_id=current_user.employee_id,
        decision=request_data.decision,
        comments=request_data.comments,
        decided_at=datetime.now(timezone.utc)
    )

    db.add(approval)

    db.commit()
    db.refresh(timesheet)

    return timesheet


# =====================================
# 5. GET - MY TIMESHEETS
# =====================================

@router.get(
    "/me",
    response_model=list[TimesheetResponse]
)
def get_my_timesheets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if not current_user.employee_id:
        raise HTTPException(
            status_code=403,
            detail="User is not linked to an employee"
        )

    return db.query(Timesheet).filter(
        Timesheet.employee_id == current_user.employee_id
    ).order_by(
        Timesheet.period_start.desc()
    ).all()


# =====================================
# 6. GET - TIMESHEET BY ID
# =====================================

@router.get(
    "/{timesheet_id}",
    response_model=TimesheetResponse
)
def get_timesheet_by_id(
    timesheet_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return get_employee_timesheet(
        db,
        timesheet_id,
        current_user
    )
