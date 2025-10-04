from __future__ import annotations

from datetime import datetime, timedelta
import random

from sqlalchemy.orm import Session

from app.db.models import Station, Measurement, FeatureSnapshot
from app.db.session import Base, engine, SessionLocal


POLLUTANTS = ["PM25", "PM10", "NO2"]
FEATURES = ["traffic_index", "industrial_activity", "dust_winds", "biomass_burning", "construction_activity"]


def seed(reset: bool = True):
    if reset:
        # Danger: drops all tables for a clean seed
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        _seed_stations(db)
        _seed_time_series(db)


def _seed_stations(db: Session):
    stations = [
        ("DEL-001", "Anand Vihar", 28.646, 77.315),
        ("DEL-002", "R K Puram", 28.566, 77.174),
        ("GUR-001", "Gurugram", 28.459, 77.026),
    ]
    for code, name, lat, lon in stations:
        if not db.query(Station).filter(Station.code == code).first():
            db.add(Station(code=code, name=name, city="Delhi-NCR", latitude=lat, longitude=lon, is_active=True))
    db.commit()


def _seed_time_series(db: Session):
    station_ids = [s.id for s in db.query(Station.id).all()]
    if not station_ids:
        return
    end = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    start = end - timedelta(days=14)
    current = start
    random.seed(42)

    while current <= end:
        for station_id in station_ids:
            feats = {name: max(0.0, random.gauss(1.0, 0.3)) for name in FEATURES}
            db.add(FeatureSnapshot(station_id=station_id, timestamp=current, data=feats))
            for pol in POLLUTANTS:
                base = 60.0 if pol == "PM25" else 100.0 if pol == "PM10" else 40.0
                variation = random.gauss(0, 10.0)
                val = max(5.0, base + variation + 5.0 * feats["traffic_index"] + 7.0 * feats["industrial_activity"]) \
                    + 3.0 * feats["construction_activity"]
                db.add(Measurement(station_id=station_id, timestamp=current, pollutant=pol, value=float(val), unit="ug/m3"))
        db.commit()
        current += timedelta(hours=1)


if __name__ == "__main__":
    seed()
