from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class MeasurementCreate(BaseModel):
    station_code: str = Field(..., description="Code of station")
    timestamp: datetime
    pollutant: str
    value: float
    unit: str = "ug/m3"


class MeasurementCreateBatch(BaseModel):
    items: List[MeasurementCreate]


class MeasurementPoint(BaseModel):
    timestamp: datetime
    value: float
    unit: str


class TimeseriesResponse(BaseModel):
    station_code: str
    pollutant: str
    points: List[MeasurementPoint]
