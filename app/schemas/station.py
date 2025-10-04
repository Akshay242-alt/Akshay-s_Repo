from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class StationBase(BaseModel):
    code: str = Field(..., description="Unique station code")
    name: str
    city: str = "Delhi"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_active: bool = True


class StationCreate(StationBase):
    pass


class StationUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_active: Optional[bool] = None


class StationOut(StationBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
