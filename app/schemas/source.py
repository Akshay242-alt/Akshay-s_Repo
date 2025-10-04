from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel


class TrainSourceRequest(BaseModel):
    pollutant: str
    station_code: Optional[str] = None
    alpha: float = 0.1


class AttributionRequest(BaseModel):
    pollutant: str
    station_code: str
    timestamp: Optional[datetime] = None


class AttributionResponse(BaseModel):
    pollutant: str
    station_code: str
    timestamp: datetime
    contributions: Dict[str, float]
    total_predicted: float
