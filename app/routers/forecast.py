from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import require_api_key
from app.db.models import ForecastModel, Station
from app.db.session import get_db
from app.schemas.forecast import ForecastResponse, TrainForecastRequest

router = APIRouter(prefix="/forecast", tags=["forecast"], dependencies=[Depends(require_api_key)])


@router.post("/train")
def train(req: TrainForecastRequest, db: Session = Depends(get_db)):
    station_id: Optional[int] = None
    if req.station_code:
        st = db.query(Station).filter(Station.code == req.station_code).first()
        if not st:
            raise HTTPException(status_code=404, detail="Station not found")
        station_id = st.id
    # Lazy import to avoid heavy deps at startup
    from app.services.forecasting import train_holt_winters
    model = train_holt_winters(db, pollutant=req.pollutant, station_id=station_id, seasonal_periods=req.seasonal_periods)
    return {"model_id": model.id, "pollutant": model.pollutant, "station_id": model.station_id, "trained_at": model.trained_at}


@router.get("/")
def get_forecast(
    pollutant: str,
    station_code: Optional[str] = None,
    horizon_hours: int = 48,
    persist: bool = False,
    db: Session = Depends(get_db),
) -> ForecastResponse:
    station_id: Optional[int] = None
    if station_code:
        st = db.query(Station).filter(Station.code == station_code).first()
        if not st:
            raise HTTPException(status_code=404, detail="Station not found")
        station_id = st.id

    model = (
        db.query(ForecastModel)
        .filter(ForecastModel.pollutant == pollutant.upper(), ForecastModel.station_id == station_id)
        .first()
    )
    if model is None:
        raise HTTPException(status_code=404, detail="No trained model")

    # Lazy import to avoid heavy deps at startup
    from app.services.forecasting import forecast as run_forecast, store_forecast
    points = run_forecast(db, model, horizon_hours=horizon_hours)
    if persist:
        store_forecast(db, model, points)
    return {
        "pollutant": model.pollutant,
        "station_code": station_code,
        "points": [{"timestamp": p.timestamp, "predicted_value": p.predicted_value} for p in points],
    }
