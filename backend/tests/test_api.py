"""FastAPI surface: health, chart, houses-only (location lock), time resolve."""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_reports_ephemeris():
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["ephemeris"]["mode"] == "swieph"
    assert "sepl_18.se1" in body["ephemeris"]["files"]


def test_resolve_time():
    r = client.post("/api/time/resolve", json={"datetime_local": "1955-01-12T07:22:00", "lat": -33.45, "lon": -70.6667})
    assert r.status_code == 200
    body = r.json()
    assert body["timezone"] == "America/Santiago"
    assert body["utc_offset"] == "-04:00"
    assert "pre_1970" in body["flags"]


def test_chart_endpoint():
    r = client.post(
        "/api/chart",
        json={
            "subject": {"datetime_local": "2024-11-03T07:50:00", "lat": 41.85, "lon": -87.65},
            "settings": {},
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["provenance"]["utc_offset"] == "-06:00"
    assert body["provenance"]["timezone"] == "America/Chicago"
    assert 210 <= body["planets"]["sun"]["lon"] < 240  # Scorpio
    assert body["houses"]["system_used"] == "placidus"
    assert len(body["houses"]["cusps"]) == 12
    assert body["planet_houses"]["sun"] == 12
    assert body["planets"]["sun"]["formatted"].startswith("11°38'")
    assert body["planets"]["jupiter"]["retrograde"] is True


def test_houses_endpoint_is_location_lock_primitive():
    r = client.post("/api/houses", json={"jd_ut": 2460618.0764, "lat": 59.9167, "lon": 10.75, "settings": {}})
    assert r.status_code == 200, r.text
    assert r.json()["system_used"] == "placidus"
    r2 = client.post("/api/houses", json={"jd_ut": 2460618.0764, "lat": 75.0, "lon": 10.75, "settings": {}})
    assert r2.json()["system_used"] == "whole_sign"
    assert r2.json()["warnings"]


def test_chart_needs_offset_on_open_ocean():
    r = client.post("/api/chart", json={"subject": {"datetime_local": "2000-01-01T12:00:00", "lat": 0, "lon": -150}, "settings": {}})
    assert r.status_code == 422
    assert "offset" in r.json()["detail"].lower()
