from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import require_api_key
from app.db.models import Station
from app.db.session import get_db
from app.schemas.station import StationCreate, StationOut, StationUpdate

router = APIRouter(prefix="/stations", tags=["stations"], dependencies=[Depends(require_api_key)])


@router.post("/", response_model=StationOut)
def create_station(payload: StationCreate, db: Session = Depends(get_db)):
    existing = db.query(Station).filter(Station.code == payload.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Station code already exists")
    st = Station(
        code=payload.code,
        name=payload.name,
        city=payload.city,
        latitude=payload.latitude,
        longitude=payload.longitude,
        is_active=payload.is_active,
    )
    db.add(st)
    db.commit()
    db.refresh(st)
    return st


@router.get("/", response_model=List[StationOut])
def list_stations(db: Session = Depends(get_db)):
    return db.query(Station).order_by(Station.code.asc()).all()


@router.get("/{code}", response_model=StationOut)
def get_station(code: str, db: Session = Depends(get_db)):
    st = db.query(Station).filter(Station.code == code).first()
    if not st:
        raise HTTPException(status_code=404, detail="Station not found")
    return st


@router.patch("/{code}", response_model=StationOut)
def update_station(code: str, payload: StationUpdate, db: Session = Depends(get_db)):
    st = db.query(Station).filter(Station.code == code).first()
    if not st:
        raise HTTPException(status_code=404, detail="Station not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(st, field, value)
    db.add(st)
    db.commit()
    db.refresh(st)
    return st
