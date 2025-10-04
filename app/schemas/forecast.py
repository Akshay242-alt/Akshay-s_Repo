from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class TrainForecastRequest(BaseModel):
    pollutant: str
    station_code: Optional[str] = None
    seasonal_periods: int = 24


class ForecastPoint(BaseModel):
    timestamp: datetime
    predicted_value: float


class ForecastResponse(BaseModel):
    pollutant: str
    station_code: Optional[str]
    points: List[ForecastPoint]
