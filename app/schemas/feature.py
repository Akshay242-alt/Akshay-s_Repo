from datetime import datetime
from typing import Dict, List

from pydantic import BaseModel


class FeatureSnapshotCreate(BaseModel):
    station_code: str
    timestamp: datetime
    data: Dict[str, float]


class FeatureSnapshotCreateBatch(BaseModel):
    items: List[FeatureSnapshotCreate]


class FeatureSnapshotOut(BaseModel):
    station_code: str
    timestamp: datetime
    data: Dict[str, float]
