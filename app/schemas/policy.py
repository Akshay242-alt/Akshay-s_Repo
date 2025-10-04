from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel


class PolicyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    # adjustments: { feature: {"multiplier": float, "delta": float} }
    adjustments: Dict[str, Dict[str, float]]


class PolicyOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    adjustments: Dict[str, Dict[str, float]]

    class Config:
        from_attributes = True


class PolicySimulationRequest(BaseModel):
    policy_id: int
    pollutant: str
    station_code: str
    timestamp: Optional[datetime] = None


class PolicySimulationResponse(BaseModel):
    policy_id: int
    pollutant: str
    station_code: str
    timestamp: datetime
    expected_value: float
    expected_change: float
