from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship

from app.db.session import Base


class Station(Base):
    __tablename__ = "stations"

    id: int = Column(Integer, primary_key=True, index=True)
    code: str = Column(String(64), unique=True, nullable=False, index=True)
    name: str = Column(String(255), nullable=False)
    city: str = Column(String(128), nullable=False, default="Delhi")
    latitude: float = Column(Float, nullable=True)
    longitude: float = Column(Float, nullable=True)
    is_active: bool = Column(Boolean, default=True)
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)

    measurements = relationship("Measurement", back_populates="station", cascade="all, delete-orphan")
    feature_snapshots = relationship("FeatureSnapshot", back_populates="station", cascade="all, delete-orphan")


class Measurement(Base):
    __tablename__ = "measurements"
    __table_args__ = (
        UniqueConstraint("station_id", "timestamp", "pollutant", name="uq_measurement_station_time_pollutant"),
        Index("ix_measurements_station_time", "station_id", "timestamp"),
    )

    id: int = Column(Integer, primary_key=True)
    station_id: int = Column(Integer, ForeignKey("stations.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp: datetime = Column(DateTime, nullable=False, index=True)
    pollutant: str = Column(String(32), nullable=False, index=True)  # e.g., PM25, PM10, NO2
    value: float = Column(Float, nullable=False)
    unit: str = Column(String(16), nullable=False, default="ug/m3")
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)

    station = relationship("Station", back_populates="measurements")


class FeatureSnapshot(Base):
    __tablename__ = "feature_snapshots"
    __table_args__ = (
        UniqueConstraint("station_id", "timestamp", name="uq_feature_station_time"),
        Index("ix_feature_station_time", "station_id", "timestamp"),
    )

    id: int = Column(Integer, primary_key=True)
    station_id: int = Column(Integer, ForeignKey("stations.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp: datetime = Column(DateTime, nullable=False, index=True)
    data: dict = Column(JSON, nullable=False, default={})
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)

    station = relationship("Station", back_populates="feature_snapshots")


class ForecastModel(Base):
    __tablename__ = "forecast_models"
    __table_args__ = (
        UniqueConstraint("pollutant", "station_id", name="uq_forecast_model_pollutant_station"),
    )

    id: int = Column(Integer, primary_key=True)
    pollutant: str = Column(String(32), nullable=False)
    station_id: Optional[int] = Column(Integer, ForeignKey("stations.id", ondelete="SET NULL"), nullable=True)
    model_type: str = Column(String(64), nullable=False, default="holt_winters")
    config: dict = Column(JSON, nullable=False, default={})
    trained_at: Optional[datetime] = Column(DateTime, nullable=True)


class Forecast(Base):
    __tablename__ = "forecasts"
    __table_args__ = (
        Index("ix_forecast_station_time", "station_id", "target_timestamp"),
    )

    id: int = Column(Integer, primary_key=True)
    model_id: int = Column(Integer, ForeignKey("forecast_models.id", ondelete="CASCADE"), nullable=False)
    station_id: Optional[int] = Column(Integer, ForeignKey("stations.id", ondelete="SET NULL"), nullable=True)
    pollutant: str = Column(String(32), nullable=False)
    target_timestamp: datetime = Column(DateTime, nullable=False)
    predicted_value: float = Column(Float, nullable=False)
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)


class SourceModel(Base):
    __tablename__ = "source_models"
    __table_args__ = (
        UniqueConstraint("pollutant", name="uq_source_model_pollutant"),
    )

    id: int = Column(Integer, primary_key=True)
    pollutant: str = Column(String(32), nullable=False)
    model_type: str = Column(String(64), nullable=False, default="lasso")
    coefficients: dict = Column(JSON, nullable=False, default={})
    intercept: float = Column(Float, nullable=False, default=0.0)
    trained_at: Optional[datetime] = Column(DateTime, nullable=True)


class SourceAttribution(Base):
    __tablename__ = "source_attributions"

    id: int = Column(Integer, primary_key=True)
    source_model_id: int = Column(Integer, ForeignKey("source_models.id", ondelete="CASCADE"), nullable=False)
    station_id: int = Column(Integer, ForeignKey("stations.id", ondelete="CASCADE"), nullable=False)
    timestamp: datetime = Column(DateTime, nullable=False)
    contributions: dict = Column(JSON, nullable=False, default={})
    total_predicted: float = Column(Float, nullable=False)
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)


class Policy(Base):
    __tablename__ = "policies"

    id: int = Column(Integer, primary_key=True)
    name: str = Column(String(128), unique=True, nullable=False)
    description: str = Column(String(1024), nullable=True)
    adjustments: dict = Column(JSON, nullable=False, default={})
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)


class PolicySimulation(Base):
    __tablename__ = "policy_simulations"

    id: int = Column(Integer, primary_key=True)
    policy_id: int = Column(Integer, ForeignKey("policies.id", ondelete="CASCADE"), nullable=False)
    station_id: Optional[int] = Column(Integer, ForeignKey("stations.id", ondelete="SET NULL"), nullable=True)
    pollutant: str = Column(String(32), nullable=False)
    start_time: Optional[datetime] = Column(DateTime, nullable=True)
    end_time: Optional[datetime] = Column(DateTime, nullable=True)
    result: dict = Column(JSON, nullable=False, default={})
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
