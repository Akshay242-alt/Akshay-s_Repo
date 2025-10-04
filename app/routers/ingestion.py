from datetime import datetime
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import require_api_key
from app.db.models import FeatureSnapshot, Measurement, Station
from app.db.session import get_db
from app.schemas.feature import FeatureSnapshotCreateBatch
from app.schemas.measurement import MeasurementCreateBatch

router = APIRouter(prefix="/ingest", tags=["ingestion"], dependencies=[Depends(require_api_key)])


@router.post("/measurements")
def ingest_measurements(batch: MeasurementCreateBatch, db: Session = Depends(get_db)):
    code_to_id: Dict[str, int] = {
        s.code: s.id for s in db.query(Station.id, Station.code).all()
    }
    created = 0
    for item in batch.items:
        station_id = code_to_id.get(item.station_code)
        if station_id is None:
            raise HTTPException(status_code=400, detail=f"Unknown station code {item.station_code}")
        m = Measurement(
            station_id=station_id,
            timestamp=item.timestamp,
            pollutant=item.pollutant.upper(),
            value=item.value,
            unit=item.unit,
        )
        try:
            db.add(m)
            db.commit()
            created += 1
        except Exception:
            db.rollback()
            # skip duplicates silently
    return {"created": created}


@router.post("/features")
def ingest_features(batch: FeatureSnapshotCreateBatch, db: Session = Depends(get_db)):
    code_to_id: Dict[str, int] = {
        s.code: s.id for s in db.query(Station.id, Station.code).all()
    }
    created = 0
    for item in batch.items:
        station_id = code_to_id.get(item.station_code)
        if station_id is None:
            raise HTTPException(status_code=400, detail=f"Unknown station code {item.station_code}")
        snap = FeatureSnapshot(
            station_id=station_id,
            timestamp=item.timestamp,
            data=item.data,
        )
        try:
            db.add(snap)
            db.commit()
            created += 1
        except Exception:
            db.rollback()
    return {"created": created}
