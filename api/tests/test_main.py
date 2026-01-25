import datetime as dt

from fastapi.testclient import TestClient

import main


class _FakeQueryJob:
    def __init__(self, rows):
        self._rows = rows

    def result(self):
        return self._rows


class _FakeClient:
    def __init__(self, rows):
        self._rows = rows
        self.last_sql = None
        self.last_job_config = None

    def query(self, sql, job_config=None):
        self.last_sql = sql
        self.last_job_config = job_config
        return _FakeQueryJob(self._rows)


def _patch_client(monkeypatch, rows):
    client = _FakeClient(rows)
    monkeypatch.setattr(main, "_client", lambda: client)
    return client


def test_health():
    client = TestClient(main.app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_twi_latest_returns_row(monkeypatch):
    _patch_client(
        monkeypatch,
        [
            {
                "base_iso": "EUR",
                "date": dt.date(2024, 1, 1),
                "rate": 123.45,
            }
        ],
    )
    client = TestClient(main.app)
    response = client.get("/twi/latest")
    assert response.status_code == 200
    assert response.json() == {
        "base_iso": "EUR",
        "date": "2024-01-01",
        "rate": 123.45,
    }


def test_twi_latest_404_when_empty(monkeypatch):
    _patch_client(monkeypatch, [])
    client = TestClient(main.app)
    response = client.get("/twi/latest")
    assert response.status_code == 404
    assert response.json()["detail"] == "No data found"


def test_twi_date_query(monkeypatch):
    _patch_client(
        monkeypatch,
        [
            {
                "base_iso": "EUR",
                "date": dt.date(2024, 1, 2),
                "rate": 101.0,
            }
        ],
    )
    client = TestClient(main.app)
    response = client.get("/twi?date=2024-01-02")
    assert response.status_code == 200
    assert response.json() == [
        {"base_iso": "EUR", "date": "2024-01-02", "rate": 101.0}
    ]


def test_twi_requires_start_and_end(monkeypatch):
    _patch_client(monkeypatch, [])
    client = TestClient(main.app)
    response = client.get("/twi?start=2024-01-01")
    assert response.status_code == 400
    assert response.json()["detail"] == "start and end must be provided together"


def test_twi_rejects_date_with_range(monkeypatch):
    _patch_client(monkeypatch, [])
    client = TestClient(main.app)
    response = client.get("/twi?date=2024-01-01&start=2024-01-01&end=2024-01-31")
    assert response.status_code == 400
    assert response.json()["detail"] == "date cannot be combined with start or end"
