from fastapi.testclient import TestClient

from app.main import app


def test_create_and_list_station(tmp_path, monkeypatch):
    # Ensure a unique in-memory DB for this test run is more complex with SQLAlchemy 2.0
    # Here we rely on app startup creating tables and using default sqlite file.
    client = TestClient(app)

    headers = {"X-API-Key": "dev-key"}

    create = client.post(
        "/api/stations/",
        json={
            "code": "TEST-001",
            "name": "Test Station",
            "city": "Delhi",
            "latitude": 28.6,
            "longitude": 77.2,
            "is_active": True,
        },
        headers=headers,
    )
    assert create.status_code in (200, 400)  # allow re-run

    res = client.get("/api/stations/", headers=headers)
    assert res.status_code == 200
    assert any(s["code"] == "TEST-001" for s in res.json())
