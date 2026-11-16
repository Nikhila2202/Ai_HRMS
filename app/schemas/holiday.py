
from pydantic import BaseModel, ConfigDict
from datetime import date
from typing import Optional


class HolidayCreate(BaseModel):
    holiday_date: date
    holiday_name: str
    country_code: str = "AE"
    region: str = "all"
    is_active: bool = True


class HolidayUpdate(BaseModel):
    holiday_date: Optional[date] = None
    holiday_name: Optional[str] = None
    country_code: Optional[str] = None
    region: Optional[str] = None
    is_active: Optional[bool] = None


class HolidayResponse(BaseModel):
    public_holiday_id: int
    holiday_date: date
    holiday_name: str
    country_code: str
    region: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
