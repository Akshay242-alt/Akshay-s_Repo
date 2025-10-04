import os
from pydantic import BaseModel


class Settings(BaseModel):
    environment: str = os.getenv("ENV", "development")
    api_prefix: str = "/api"
    api_key: str = os.getenv("API_KEY", "dev-key")

    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")

    # Modeling
    forecast_horizon_hours: int = 48


settings = Settings()
