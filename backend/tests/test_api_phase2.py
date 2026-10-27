"""Phase 2 API: chart at any instant (single + batch), cities, subjects CRUD."""
from __future__ import annotations

from fastapi.testclient import TestClient

from app import main as main_module
from app.engine.chart import calculate_chart
from app.engine.models import ChartInput, Settings
from app.main import app

client = TestClient(app)


def test_chart_at_matches_calculate_chart():
    base = calculate_chart(ChartInput(datetime_local="2024-11-03T07:50:00", lat=41.85, lon=-87.65), Settings())
    r = client.post("/api/chart/at", json={"jd_ut": base.moment.jd_ut, "lat": 41.85, "lon": -87.65, "settings": {}})
    assert r.status_code == 200, r.text
    body = r.json()
    assert abs(body["planets"]["sun"]["lon"] - base.planets["sun"].lon) < 1e-9
    assert abs(body["houses"]["asc"] - base.houses.asc) < 1e-9
    assert body["planet_houses"]["sun"] == 12
    assert body["moment"]["utc_datetime"].startswith("2024-11-03T13:50")
    assert "aspects" in body and any(a["type"] == "conjunction" for a in body["aspects"])


def test_chart_at_batch_keyframes():
    jd = 2460618.0764
    r = client.post("/api/chart/at/batch", json={"jd_uts": [jd, jd + 1 / 24, jd + 2 / 24], "lat": 41.85, "lon": -87.65, "settings": {}})
    assert r.status_code == 200, r.text
    frames = r.json()["frames"]
    assert len(frames) == 3
    assert frames[0]["jd_ut"] == jd
    assert set(frames[0]["planets"]) >= {"sun", "moon", "pluto"}
    assert len(frames[0]["cusps"]) == 12
    # ASC advances about 15 degrees per hour at this latitude
    assert 8 < (frames[1]["asc"] - frames[0]["asc"]) % 360 < 25


def test_chart_includes_aspects_and_settings_round_trip():
    r = client.post("/api/chart", json={"subject": {"datetime_local": "1992-07-23T04:23:00", "lat": 59.9167, "lon": 10.75},
                                        "settings": {"aspects": {"orbs": {"conjunction": 1}}}})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["settings"]["aspects"]["orbs"]["conjunction"] == 1
    assert body["settings"]["aspects"]["orbs"]["trine"] == 8


def test_cities_endpoint(tmp_path, monkeypatch):
    from app.cities import CityIndex
    src = tmp_path / "c.txt"
    src.write_text("3143244\tOslo\tOslo\tOslo\t59.91273\t10.74609\tP\tPPLC\tNO\t\t12\t\t\t\t580000\t\t26\tEurope/Oslo\t2019-01-01\n")
    idx = CityIndex(tmp_path / "cities.sqlite"); idx.build_from_file(src)
    monkeypatch.setattr(main_module, "city_index", lambda: idx)
    r = client.get("/api/cities", params={"q": "os"})
    assert r.status_code == 200
    assert r.json()[0]["name"] == "Oslo" and r.json()[0]["timezone"] == "Europe/Oslo"


def test_subjects_crud(tmp_path, monkeypatch):
    from app.storage import ChartLibrary
    lib = ChartLibrary(db_path=tmp_path / "charts.sqlite", key_path=tmp_path / "charts.key")
    monkeypatch.setattr(main_module, "library", lambda: lib)
    payload = {"name": "Golden Oslo", "kind": "person", "tags": ["golden"], "notes": "", "datetime_local": "1992-07-23T04:23:00",
               "time_confidence": "exact", "place_name": "Oslo", "lat": 59.9167, "lon": 10.75, "timezone": "Europe/Oslo",
               "utc_offset_override": None, "settings": {}}
    r = client.post("/api/subjects", json=payload)
    assert r.status_code == 201, r.text
    sid = r.json()["id"]
    assert client.get("/api/subjects").json()[0]["name"] == "Golden Oslo"
    assert client.get("/api/subjects", params={"q": "gold"}).json()[0]["id"] == sid
    r = client.put(f"/api/subjects/{sid}", json={**payload, "name": "Golden Oslo 2"})
    assert r.json()["name"] == "Golden Oslo 2"
    r = client.get(f"/api/subjects/{sid}/chart")
    assert r.status_code == 200 and r.json()["provenance"]["timezone"] == "Europe/Oslo"
    assert client.delete(f"/api/subjects/{sid}").status_code == 204
    assert client.get("/api/subjects").json() == []
    assert client.get(f"/api/subjects/{sid}").status_code == 200  # still readable, soft deleted
    assert client.post(f"/api/subjects/{sid}/restore").status_code == 200
    assert len(client.get("/api/subjects").json()) == 1
    assert client.get("/api/subjects/zzz").status_code == 404
