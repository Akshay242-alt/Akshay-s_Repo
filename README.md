# Delhi-NCR AI Pollution Backend

FastAPI backend providing ingestion, querying, forecasting, source apportionment, and policy simulation for Delhi-NCR air quality.

## Quickstart

### Local (no Docker)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export API_KEY=dev-key
uvicorn app.main:app --reload
```

Seed synthetic data:

```bash
python3 -m app.utils.seed
```

### Docker

```bash
docker build -t delhi-ai-aq-backend .
docker run -p 8000:8000 -e API_KEY=dev-key -v $(pwd)/data:/app/data delhi-ai-aq-backend
```

## API Overview

- GET `/api/health`
- Stations: `/api/stations`
- Ingestion: `/api/ingest/measurements`, `/api/ingest/features`
- Query: `/api/query/current`, `/api/query/timeseries`
- Forecast: `/api/forecast/train`, `/api/forecast`
- Source: `/api/source/train`, `/api/source/attribute`
- Policy: `/api/policy/`, `/api/policy/simulate`

Auth: header `X-API-Key: <API_KEY>`
