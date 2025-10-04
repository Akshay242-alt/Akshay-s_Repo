from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

import numpy as np

# Lazy import to avoid heavy import at startup
def _get_hw():
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    return ExponentialSmoothing
from sqlalchemy.orm import Session

from app.db.models import Forecast, ForecastModel, Measurement, Station


@dataclass
class ForecastPointDTO:
    timestamp: datetime
    predicted_value: float


def load_series(db: Session, station_id: Optional[int], pollutant: str) -> Tuple[np.ndarray, List[datetime]]:
    q = db.query(Measurement).filter(Measurement.pollutant == pollutant.upper())
    if station_id is not None:
        q = q.filter(Measurement.station_id == station_id)
    rows = q.order_by(Measurement.timestamp.asc()).all()
    values = np.array([r.value for r in rows], dtype=float)
    times = [r.timestamp for r in rows]
    return values, times


def train_holt_winters(db: Session, pollutant: str, station_id: Optional[int], seasonal_periods: int = 24) -> ForecastModel:
    values, times = load_series(db, station_id, pollutant)
    if len(values) < seasonal_periods * 2:
        raise ValueError("Not enough data to train model")
    ExponentialSmoothing = _get_hw()
    model = ExponentialSmoothing(values, seasonal='add', seasonal_periods=seasonal_periods, trend='add').fit()

    fm = db.query(ForecastModel).filter(
        ForecastModel.pollutant == pollutant.upper(),
        ForecastModel.station_id == station_id,
    ).first()
    if fm is None:
        fm = ForecastModel(pollutant=pollutant.upper(), station_id=station_id, model_type="holt_winters", config={})
        db.add(fm)
    fm.config = {"params": model.params.__dict__}
    fm.trained_at = datetime.utcnow()
    db.commit()
    db.refresh(fm)
    return fm


def forecast(db: Session, model: ForecastModel, horizon_hours: int = 48) -> List[ForecastPointDTO]:
    values, times = load_series(db, model.station_id, model.pollutant)
    if len(values) < 10:
        raise ValueError("Not enough data to forecast")
    seasonal_periods = model.config.get("params", {}).get("seasonal_periods", 24)
    ExponentialSmoothing = _get_hw()
    hw = ExponentialSmoothing(values, seasonal='add', seasonal_periods=seasonal_periods, trend='add').fit()
    steps = horizon_hours
    preds = hw.forecast(steps)
    last_time = times[-1] if times else datetime.utcnow()
    points: List[ForecastPointDTO] = []
    for i in range(1, steps + 1):
        points.append(ForecastPointDTO(timestamp=last_time + timedelta(hours=i), predicted_value=float(preds[i - 1])))
    return points


def store_forecast(db: Session, model: ForecastModel, points: List[ForecastPointDTO]) -> None:
    for p in points:
        f = Forecast(
            model_id=model.id,
            station_id=model.station_id,
            pollutant=model.pollutant,
            target_timestamp=p.timestamp,
            predicted_value=p.predicted_value,
        )
        db.add(f)
    db.commit()
