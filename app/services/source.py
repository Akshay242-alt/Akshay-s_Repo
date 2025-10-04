from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np
def _get_lasso():
    from sklearn.linear_model import Lasso
    return Lasso
from sqlalchemy.orm import Session

from app.db.models import FeatureSnapshot, Measurement, SourceAttribution, SourceModel, Station


@dataclass
class AttributionDTO:
    timestamp: datetime
    contributions: Dict[str, float]
    total_predicted: float


def load_dataset(
    db: Session, station_id: Optional[int], pollutant: str
) -> Tuple[np.ndarray, np.ndarray, List[str], List[datetime]]:
    # Build in-memory feature alignment by timestamp
    q_meas = db.query(Measurement).filter(Measurement.pollutant == pollutant.upper())
    if station_id is not None:
        q_meas = q_meas.filter(Measurement.station_id == station_id)
    meas_rows = q_meas.all()

    # Index feature snapshots by (station_id, timestamp)
    feat_map: Dict[Tuple[int, datetime], Dict[str, float]] = {}
    for snap in db.query(FeatureSnapshot).all():
        feat_map[(snap.station_id, snap.timestamp)] = snap.data

    # Collect aligned X, y where both measurement and features exist
    feature_names: List[str] = []
    X_list: List[List[float]] = []
    y_list: List[float] = []
    times: List[datetime] = []

    for m in meas_rows:
        feats = feat_map.get((m.station_id, m.timestamp))
        if feats is None:
            continue
        if not feature_names:
            feature_names = sorted(feats.keys())
        x = [float(feats.get(name, 0.0)) for name in feature_names]
        X_list.append(x)
        y_list.append(float(m.value))
        times.append(m.timestamp)

    if not X_list:
        return np.zeros((0, 0)), np.zeros((0,)), feature_names, times
    X = np.array(X_list, dtype=float)
    y = np.array(y_list, dtype=float)
    return X, y, feature_names, times


def train_lasso(db: Session, pollutant: str, station_id: Optional[int], alpha: float = 0.1) -> SourceModel:
    X, y, feature_names, times = load_dataset(db, station_id, pollutant)
    if X.shape[0] < 10 or X.shape[1] == 0:
        raise ValueError("Insufficient data for training source model")
    Lasso = _get_lasso()
    model = Lasso(alpha=alpha)
    model.fit(X, y)

    sm = db.query(SourceModel).filter(SourceModel.pollutant == pollutant.upper()).first()
    if sm is None:
        sm = SourceModel(pollutant=pollutant.upper(), model_type="lasso", coefficients={}, intercept=0.0)
        db.add(sm)
    sm.coefficients = {name: float(coeff) for name, coeff in zip(feature_names, model.coef_)}
    sm.intercept = float(model.intercept_)
    sm.trained_at = datetime.utcnow()
    db.commit()
    db.refresh(sm)
    return sm


def attribute_sources(
    db: Session, source_model: SourceModel, station_id: int, timestamp: datetime, features: Dict[str, float]
) -> AttributionDTO:
    # Predict and decompose into contributions
    contributions: Dict[str, float] = {}
    total_pred = source_model.intercept
    for name, coeff in source_model.coefficients.items():
        val = float(features.get(name, 0.0))
        contrib = coeff * val
        contributions[name] = contrib
        total_pred += contrib
    return AttributionDTO(timestamp=timestamp, contributions=contributions, total_predicted=total_pred)


def store_attribution(
    db: Session, source_model: SourceModel, station_id: int, dto: AttributionDTO
) -> None:
    sa = SourceAttribution(
        source_model_id=source_model.id,
        station_id=station_id,
        timestamp=dto.timestamp,
        contributions=dto.contributions,
        total_predicted=dto.total_predicted,
    )
    db.add(sa)
    db.commit()
