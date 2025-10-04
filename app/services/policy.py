from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional

from sqlalchemy.orm import Session

from app.db.models import FeatureSnapshot, Policy, PolicySimulation, Station, SourceModel


def create_policy(db: Session, name: str, description: Optional[str], adjustments: Dict[str, Dict[str, float]]) -> Policy:
    pol = Policy(name=name, description=description, adjustments=adjustments)
    db.add(pol)
    db.commit()
    db.refresh(pol)
    return pol


def apply_adjustments(features: Dict[str, float], adjustments: Dict[str, Dict[str, float]]) -> Dict[str, float]:
    out: Dict[str, float] = dict(features)
    for feat, rule in adjustments.items():
        mult = float(rule.get("multiplier", 1.0))
        delta = float(rule.get("delta", 0.0))
        out[feat] = out.get(feat, 0.0) * mult + delta
    return out


def simulate_policy(
    db: Session,
    policy: Policy,
    station_id: int,
    pollutant: str,
    timestamp: Optional[datetime],
) -> PolicySimulation:
    # find feature snapshot at timestamp or latest before
    q = db.query(FeatureSnapshot).filter(FeatureSnapshot.station_id == station_id)
    if timestamp is not None:
        q = q.filter(FeatureSnapshot.timestamp <= timestamp)
    snap = q.order_by(FeatureSnapshot.timestamp.desc()).first()
    if snap is None:
        raise ValueError("No feature snapshot available for simulation")

    adjusted = apply_adjustments(snap.data, policy.adjustments)

    # simple evaluation using source model coefficients
    sm = db.query(SourceModel).filter(SourceModel.pollutant == pollutant.upper()).first()
    if sm is None:
        raise ValueError("No source model available")

    def predict(coeffs: Dict[str, float], intercept: float, feats: Dict[str, float]) -> float:
        total = intercept
        for name, coeff in coeffs.items():
            total += coeff * float(feats.get(name, 0.0))
        return float(total)

    base_value = predict(sm.coefficients, sm.intercept, snap.data)
    adjusted_value = predict(sm.coefficients, sm.intercept, adjusted)

    sim = PolicySimulation(
        policy_id=policy.id,
        station_id=station_id,
        pollutant=pollutant.upper(),
        start_time=snap.timestamp,
        end_time=snap.timestamp,
        result={
            "base_value": base_value,
            "adjusted_value": adjusted_value,
            "expected_change": adjusted_value - base_value,
        },
    )
    db.add(sim)
    db.commit()
    db.refresh(sim)
    return sim
