from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import require_api_key
from app.db.models import Policy, Station
from app.db.session import get_db
from app.schemas.policy import PolicyCreate, PolicyOut, PolicySimulationRequest, PolicySimulationResponse
from app.services.policy import create_policy, simulate_policy

router = APIRouter(prefix="/policy", tags=["policy"], dependencies=[Depends(require_api_key)])


@router.post("/", response_model=PolicyOut)
def create(payload: PolicyCreate, db: Session = Depends(get_db)):
    if db.query(Policy).filter(Policy.name == payload.name).first():
        raise HTTPException(status_code=400, detail="Policy name exists")
    pol = create_policy(db, payload.name, payload.description, payload.adjustments)
    return pol


@router.post("/simulate", response_model=PolicySimulationResponse)
def simulate(req: PolicySimulationRequest, db: Session = Depends(get_db)):
    pol = db.query(Policy).filter(Policy.id == req.policy_id).first()
    if not pol:
        raise HTTPException(status_code=404, detail="Policy not found")
    st = db.query(Station).filter(Station.code == req.station_code).first()
    if not st:
        raise HTTPException(status_code=404, detail="Station not found")
    sim = simulate_policy(db, pol, st.id, req.pollutant, req.timestamp)
    return PolicySimulationResponse(
        policy_id=pol.id,
        pollutant=req.pollutant.upper(),
        station_code=req.station_code,
        timestamp=sim.start_time or datetime.utcnow(),
        expected_value=sim.result.get("adjusted_value", 0.0),
        expected_change=sim.result.get("expected_change", 0.0),
    )
