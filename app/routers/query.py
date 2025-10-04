from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query as Q
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.core.security import require_api_key
from app.db.models import Measurement, Station
from app.db.session import get_db
from app.schemas.measurement import TimeseriesResponse, MeasurementPoint

router = APIRouter(prefix="/query", tags=["query"], dependencies=[Depends(require_api_key)])


@router.get("/current")
def current_air_quality(
    station_code: str,
    pollutant: str,
    db: Session = Depends(get_db),
):
    st = db.query(Station).filter(Station.code == station_code).first()
    if not st:
        raise HTTPException(status_code=404, detail="Station not found")
    row = (
        db.query(Measurement)
        .filter(
            Measurement.station_id == st.id,
            Measurement.pollutant == pollutant.upper(),
        )
        .order_by(Measurement.timestamp.desc())
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="No measurements")
    return {
        "station_code": station_code,
        "pollutant": pollutant.upper(),
        "timestamp": row.timestamp,
        "value": row.value,
        "unit": row.unit,
    }


@router.get("/timeseries", response_model=TimeseriesResponse)
def timeseries(
    station_code: str,
    pollutant: str,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    limit: int = 1000,
    db: Session = Depends(get_db),
):
    st = db.query(Station).filter(Station.code == station_code).first()
    if not st:
        raise HTTPException(status_code=404, detail="Station not found")

    q = db.query(Measurement).filter(
        Measurement.station_id == st.id,
        Measurement.pollutant == pollutant.upper(),
    )
    if start is not None:
        q = q.filter(Measurement.timestamp >= start)
    if end is not None:
        q = q.filter(Measurement.timestamp <= end)
    rows = q.order_by(Measurement.timestamp.asc()).limit(limit).all()
    points = [MeasurementPoint(timestamp=r.timestamp, value=r.value, unit=r.unit) for r in rows]
    return TimeseriesResponse(station_code=station_code, pollutant=pollutant.upper(), points=points)
