from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import require_api_key
from app.db.models import FeatureSnapshot, SourceModel, Station
from app.db.session import get_db
from app.schemas.source import AttributionRequest, AttributionResponse, TrainSourceRequest
from app.services.source import attribute_sources, store_attribution

router = APIRouter(prefix="/source", tags=["source"], dependencies=[Depends(require_api_key)])


@router.post("/train")
def train(req: TrainSourceRequest, db: Session = Depends(get_db)):
    station_id: Optional[int] = None
    if req.station_code:
        st = db.query(Station).filter(Station.code == req.station_code).first()
        if not st:
            raise HTTPException(status_code=404, detail="Station not found")
        station_id = st.id
    # Lazy import heavy dep
    from app.services.source import train_lasso
    model = train_lasso(db, pollutant=req.pollutant, station_id=station_id, alpha=req.alpha)
    return {"model_id": model.id, "pollutant": model.pollutant, "trained_at": model.trained_at}


@router.post("/attribute", response_model=AttributionResponse)
def attribute(req: AttributionRequest, db: Session = Depends(get_db)):
    st = db.query(Station).filter(Station.code == req.station_code).first()
    if not st:
        raise HTTPException(status_code=404, detail="Station not found")

    model = db.query(SourceModel).filter(SourceModel.pollutant == req.pollutant.upper()).first()
    if model is None:
        raise HTTPException(status_code=404, detail="No trained source model")

    # get features at timestamp or latest
    q = db.query(FeatureSnapshot).filter(FeatureSnapshot.station_id == st.id)
    if req.timestamp is not None:
        q = q.filter(FeatureSnapshot.timestamp <= req.timestamp)
    snap = q.order_by(FeatureSnapshot.timestamp.desc()).first()
    if snap is None:
        raise HTTPException(status_code=404, detail="No feature snapshot")

    dto = attribute_sources(db, model, st.id, snap.timestamp, snap.data)
    store_attribution(db, model, st.id, dto)
    return AttributionResponse(
        pollutant=req.pollutant.upper(),
        station_code=req.station_code,
        timestamp=dto.timestamp,
        contributions=dto.contributions,
        total_predicted=dto.total_predicted,
    )
