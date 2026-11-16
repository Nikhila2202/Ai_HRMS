
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database import get_db

from app.models.model import PublicHoliday

from app.schemas.holiday import (
    HolidayCreate,
    HolidayUpdate,
    HolidayResponse
)


router = APIRouter(
    prefix="/holidays",
    tags=["Public Holidays"]
)


# 1. GET ALL HOLIDAYS

@router.get("/", response_model=list[HolidayResponse])
def get_holidays(
    db: Session = Depends(get_db)
):

    holidays = db.query(PublicHoliday).order_by(
        PublicHoliday.holiday_date.asc()
    ).all()

    return holidays


# 2. GET HOLIDAY BY ID

@router.get("/{holiday_id}", response_model=HolidayResponse)
def get_holiday_by_id(
    holiday_id: int,
    db: Session = Depends(get_db)
):

    holiday = db.query(PublicHoliday).filter(
        PublicHoliday.public_holiday_id == holiday_id
    ).first()

    if not holiday:
        raise HTTPException(
            status_code=404,
            detail="Holiday not found"
        )

    return holiday


# 3. POST CREATE HOLIDAY

@router.post(
    "/",
    response_model=HolidayResponse,
    status_code=status.HTTP_201_CREATED
)
def create_holiday(
    holiday_data: HolidayCreate,
    db: Session = Depends(get_db)
):

    # Check duplicate holiday

    existing_holiday = db.query(PublicHoliday).filter(
        PublicHoliday.holiday_date == holiday_data.holiday_date,
        PublicHoliday.country_code == holiday_data.country_code,
        PublicHoliday.region == holiday_data.region
    ).first()

    if existing_holiday:
        raise HTTPException(
            status_code=409,
            detail="Holiday already exists for this date, country and region"
        )

    new_holiday = PublicHoliday(
        holiday_date=holiday_data.holiday_date,
        holiday_name=holiday_data.holiday_name,
        country_code=holiday_data.country_code.upper(),
        region=holiday_data.region,
        is_active=holiday_data.is_active
    )

    try:
        db.add(new_holiday)
        db.commit()
        db.refresh(new_holiday)

        return new_holiday

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Duplicate holiday record"
        )


# 4. PATCH UPDATE HOLIDAY BY ID

@router.patch(
    "/{holiday_id}",
    response_model=HolidayResponse
)
def update_holiday(
    holiday_id: int,
    holiday_data: HolidayUpdate,
    db: Session = Depends(get_db)
):

    holiday = db.query(PublicHoliday).filter(
        PublicHoliday.public_holiday_id == holiday_id
    ).first()

    if not holiday:
        raise HTTPException(
            status_code=404,
            detail="Holiday not found"
        )

    update_data = holiday_data.model_dump(
        exclude_unset=True
    )

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No fields provided for update"
        )

    if "country_code" in update_data:
        update_data["country_code"] = (
            update_data["country_code"].upper()
        )

    # Check uniqueness if unique fields are updated

    new_date = update_data.get(
        "holiday_date", holiday.holiday_date
    )

    new_country = update_data.get(
        "country_code", holiday.country_code
    )

    new_region = update_data.get(
        "region", holiday.region
    )

    duplicate = db.query(PublicHoliday).filter(
        PublicHoliday.holiday_date == new_date,
        PublicHoliday.country_code == new_country,
        PublicHoliday.region == new_region,
        PublicHoliday.public_holiday_id != holiday_id
    ).first()

    if duplicate:
        raise HTTPException(
            status_code=409,
            detail="Another holiday already exists for this date, country and region"
        )

    try:
        for field, value in update_data.items():
            setattr(holiday, field, value)

        db.commit()
        db.refresh(holiday)

        return holiday

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Duplicate holiday record"
        )
